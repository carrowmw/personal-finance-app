import {
  BadRequestException,
  Inject,
  Injectable,
  NotFoundException,
  ServiceUnavailableException,
} from "@nestjs/common";
import { createCipheriv, createDecipheriv, randomBytes } from "node:crypto";
import { ConfigService } from "@nestjs/config";
import { Prisma } from "@prisma/client";
import {
  Configuration,
  CountryCode,
  PlaidApi,
  PlaidEnvironments,
  Products,
  Transaction,
  TransactionsSyncRequest,
} from "plaid";

import { PrismaService } from "../common/prisma.service.js";

@Injectable()
export class PlaidService {
  private static readonly ENCRYPTION_PREFIX = "enc:v1:";

  private readonly plaidClient: PlaidApi;
  private readonly plaidClientId: string | undefined;
  private readonly plaidSecret: string | undefined;
  private readonly products: Products[];
  private readonly countryCodes: CountryCode[];
  private readonly personalFinanceTaxonomyVersion: string | null;
  private readonly plaidRedirectUri: string | null;
  private readonly accessTokenKey: Buffer | null;

  constructor(
    @Inject(ConfigService) private readonly configService: ConfigService,
    @Inject(PrismaService) private readonly prisma: PrismaService,
  ) {
    this.plaidClientId = this.configService.get<string>("PLAID_CLIENT_ID");
    const plaidEnv = this.configService.get<string>("PLAID_ENV", "sandbox");

    const legacySecret = this.configService.get<string>("PLAID_SECRET");
    const sandboxSecret = this.configService.get<string>(
      "PLAID_SANDBOX_SECRET",
    );
    const developmentSecret = this.configService.get<string>(
      "PLAID_DEVELOPMENT_SECRET",
    );
    const productionSecret = this.configService.get<string>(
      "PLAID_PRODUCTION_SECRET",
    );

    this.plaidSecret =
      (plaidEnv === "production" ? productionSecret : undefined) ??
      (plaidEnv === "development" ? developmentSecret : undefined) ??
      (plaidEnv === "sandbox" ? sandboxSecret : undefined) ??
      legacySecret;

    this.products = this.configService
      .get<string>("PLAID_PRODUCTS", "transactions")
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean) as Products[];

    this.countryCodes = this.configService
      .get<string>("PLAID_COUNTRY_CODES", "US")
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean) as CountryCode[];

    this.personalFinanceTaxonomyVersion =
      this.configService.get<string>("PLAID_PFC_TAXONOMY_VERSION") ?? null;
    this.plaidRedirectUri =
      this.configService.get<string>("PLAID_REDIRECT_URI") ?? null;

    const rawAccessTokenKey = this.configService.get<string>(
      "PLAID_ACCESS_TOKEN_ENCRYPTION_KEY",
    );
    this.accessTokenKey = rawAccessTokenKey
      ? Buffer.from(rawAccessTokenKey, "base64")
      : null;

    this.plaidClient = new PlaidApi(
      new Configuration({
        basePath: PlaidEnvironments[plaidEnv as keyof typeof PlaidEnvironments],
        baseOptions: {
          headers: {
            "PLAID-CLIENT-ID": this.plaidClientId ?? "",
            "PLAID-SECRET": this.plaidSecret ?? "",
          },
        },
      }),
    );
  }

  async createLinkToken(userId: string): Promise<{ linkToken: string }> {
    this.ensurePlaidConfigured();
    await this.ensureUserExists(userId);

    const request = {
      user: {
        client_user_id: userId,
      },
      client_name: "Personal Finances",
      products: this.products,
      country_codes: this.countryCodes,
      language: "en",
      ...(this.plaidRedirectUri ? { redirect_uri: this.plaidRedirectUri } : {}),
    };

    const response = await this.plaidClient.linkTokenCreate(request);

    return {
      linkToken: response.data.link_token,
    };
  }

  async exchangePublicToken(
    userId: string,
    publicToken: string,
  ): Promise<{ userId: string; linked: boolean }> {
    this.ensurePlaidConfigured();
    await this.ensureUserExists(userId);

    const exchangeResponse = await this.plaidClient.itemPublicTokenExchange({
      public_token: publicToken,
    });

    await this.prisma.plaidItem.upsert({
      where: {
        plaidItemId: exchangeResponse.data.item_id,
      },
      create: {
        userId,
        plaidItemId: exchangeResponse.data.item_id,
        accessToken: this.encryptAccessToken(
          exchangeResponse.data.access_token,
        ),
      },
      update: {
        userId,
        accessToken: this.encryptAccessToken(
          exchangeResponse.data.access_token,
        ),
      },
    });

    return {
      userId,
      linked: true,
    };
  }

  async syncTransactions(userId: string): Promise<number> {
    this.ensurePlaidConfigured();

    const plaidItem = await this.prisma.plaidItem.findFirst({
      where: { userId },
      orderBy: { createdAt: "asc" },
    });

    if (!plaidItem) {
      throw new NotFoundException("No linked Plaid item found for user");
    }

    const syncState = await this.prisma.syncState.findUnique({
      where: { plaidItemId: plaidItem.id },
    });

    let cursor = syncState?.cursor ?? undefined;
    let hasMore = true;
    let processedCount = 0;

    while (hasMore) {
      const request: TransactionsSyncRequest = {
        access_token: this.decryptAccessToken(plaidItem.accessToken),
        cursor,
        count: 100,
      };

      try {
        const response = await this.plaidClient.transactionsSync(request);
        const data = response.data;
        const transactionsToProcess = [...data.added, ...data.modified];

        // 1. Optimize Account Upserts (Deduplicate and run sequentially to avoid DB deadlocks)
        const uniqueAccountIds = Array.from(
          new Set(transactionsToProcess.map((t) => t.account_id)),
        );
        const accountMap = new Map<string, string>(); // Maps Plaid ID to Internal DB ID

        for (const accountId of uniqueAccountIds) {
          const account = await this.prisma.account.upsert({
            where: { plaidAccountId: accountId },
            create: {
              userId,
              plaidItemId: plaidItem.id,
              plaidAccountId: accountId,
              name: "Plaid Account",
              type: "depository",
            },
            update: {},
          });
          accountMap.set(accountId, account.id);
        }

        // 2. Optimize Transaction Upserts (Run all 100 concurrently!)
        await Promise.all(
          transactionsToProcess.map(async (transaction) => {
            const financeCategory = transaction.personal_finance_category;
            const legacyCategory = transaction.category ?? [];
            const primaryCategory =
              financeCategory?.primary ?? legacyCategory[0] ?? null;
            const detailedCategory =
              financeCategory?.detailed ??
              legacyCategory[1] ??
              legacyCategory[0] ??
              null;
            const confidenceLevel = financeCategory?.confidence_level ?? null;
            const taxonomyVersion = financeCategory
              ? this.personalFinanceTaxonomyVersion
              : null;
            const date = new Date(transaction.date);

            return this.prisma.transaction.upsert({
              where: {
                plaidTransactionId: transaction.transaction_id,
              },
              create: {
                userId,
                accountId: accountMap.get(transaction.account_id)!,
                plaidTransactionId: transaction.transaction_id,
                amount: new Prisma.Decimal(transaction.amount),
                name: transaction.name,
                merchantName: transaction.merchant_name ?? null,
                pending: transaction.pending,
                categoryPrimary: primaryCategory,
                categoryDetailed: detailedCategory,
                categoryConfidenceLevel: confidenceLevel,
                categoryTaxonomyVersion: taxonomyVersion,
                isoCurrencyCode: transaction.iso_currency_code ?? null,
                date,
              },
              update: {
                amount: new Prisma.Decimal(transaction.amount),
                name: transaction.name,
                merchantName: transaction.merchant_name ?? null,
                pending: transaction.pending,
                categoryPrimary: primaryCategory,
                categoryDetailed: detailedCategory,
                categoryConfidenceLevel: confidenceLevel,
                categoryTaxonomyVersion: taxonomyVersion,
                isoCurrencyCode: transaction.iso_currency_code ?? null,
                date,
              },
            });
          }),
        );

        // 3. Handle deletions
        if (data.removed.length > 0) {
          const removedIds = data.removed.map((entry) => entry.transaction_id);
          await this.prisma.transaction.deleteMany({
            where: {
              plaidTransactionId: { in: removedIds },
              userId,
            },
          });
        }

        processedCount +=
          data.added.length + data.modified.length + data.removed.length;

        cursor = data.next_cursor;
        hasMore = data.has_more;
      } catch (error: any) {
        // Catch Plaid's pagination mutation error
        if (
          error.response?.data?.error_code ===
          "TRANSACTIONS_SYNC_MUTATION_DURING_PAGINATION"
        ) {
          break;
        }
        throw error;
      }
    }

    await this.prisma.syncState.upsert({
      where: {
        plaidItemId: plaidItem.id,
      },
      create: {
        plaidItemId: plaidItem.id,
        cursor: cursor ?? null,
      },
      update: {
        cursor: cursor ?? null,
      },
    });

    return processedCount;
  }

  async reencryptLegacyAccessTokens(): Promise<{
    scanned: number;
    updated: number;
  }> {
    this.ensurePlaidConfigured();

    const legacyItems = await this.prisma.plaidItem.findMany({
      where: {
        NOT: {
          accessToken: {
            startsWith: PlaidService.ENCRYPTION_PREFIX,
          },
        },
      },
      select: {
        id: true,
        accessToken: true,
      },
    });

    for (const item of legacyItems) {
      await this.prisma.plaidItem.update({
        where: { id: item.id },
        data: {
          accessToken: this.encryptAccessToken(item.accessToken),
        },
      });
    }

    return {
      scanned: legacyItems.length,
      updated: legacyItems.length,
    };
  }

  private ensurePlaidConfigured(): void {
    if (!this.plaidClientId || !this.plaidSecret) {
      throw new ServiceUnavailableException("Missing Plaid credentials");
    }

    if (!this.accessTokenKey || this.accessTokenKey.length !== 32) {
      throw new ServiceUnavailableException(
        "Invalid PLAID_ACCESS_TOKEN_ENCRYPTION_KEY. Expected a base64-encoded 32-byte key.",
      );
    }
  }

  private async ensureUserExists(userId: string): Promise<void> {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user) {
      throw new BadRequestException("Unknown user");
    }
  }

  private encryptAccessToken(rawToken: string): string {
    const key = this.getAccessTokenKeyOrThrow();
    const iv = randomBytes(12);
    const cipher = createCipheriv("aes-256-gcm", key, iv);
    const encrypted = Buffer.concat([
      cipher.update(rawToken, "utf8"),
      cipher.final(),
    ]);
    const authTag = cipher.getAuthTag();
    return `${PlaidService.ENCRYPTION_PREFIX}${iv.toString("base64")}.${authTag.toString("base64")}.${encrypted.toString("base64")}`;
  }

  private decryptAccessToken(storedValue: string): string {
    if (!storedValue.startsWith(PlaidService.ENCRYPTION_PREFIX)) {
      throw new ServiceUnavailableException(
        "Found legacy unencrypted Plaid token. Run the re-encryption maintenance task first.",
      );
    }

    const key = this.getAccessTokenKeyOrThrow();
    const payload = storedValue.slice(PlaidService.ENCRYPTION_PREFIX.length);
    const [ivB64, authTagB64, ciphertextB64] = payload.split(".");

    if (!ivB64 || !authTagB64 || !ciphertextB64) {
      throw new ServiceUnavailableException(
        "Stored Plaid token has invalid format",
      );
    }

    const iv = Buffer.from(ivB64, "base64");
    const authTag = Buffer.from(authTagB64, "base64");
    const ciphertext = Buffer.from(ciphertextB64, "base64");

    const decipher = createDecipheriv("aes-256-gcm", key, iv);
    decipher.setAuthTag(authTag);
    const decrypted = Buffer.concat([
      decipher.update(ciphertext),
      decipher.final(),
    ]);
    return decrypted.toString("utf8");
  }

  private getAccessTokenKeyOrThrow(): Buffer {
    if (!this.accessTokenKey || this.accessTokenKey.length !== 32) {
      throw new ServiceUnavailableException(
        "Invalid PLAID_ACCESS_TOKEN_ENCRYPTION_KEY. Expected a base64-encoded 32-byte key.",
      );
    }

    return this.accessTokenKey;
  }

  private async upsertTransaction(
    userId: string,
    plaidItemId: string,
    transaction: Transaction,
  ): Promise<void> {
    const account = await this.prisma.account.upsert({
      where: {
        plaidAccountId: transaction.account_id,
      },
      create: {
        userId,
        plaidItemId,
        plaidAccountId: transaction.account_id,
        name: "Plaid Account",
        type: "depository",
      },
      update: {},
    });

    const financeCategory = transaction.personal_finance_category;
    const legacyCategory = transaction.category ?? [];
    const primaryCategory =
      financeCategory?.primary ?? legacyCategory[0] ?? null;
    const detailedCategory =
      financeCategory?.detailed ??
      legacyCategory[1] ??
      legacyCategory[0] ??
      null;
    const confidenceLevel = financeCategory?.confidence_level ?? null;
    const taxonomyVersion = financeCategory
      ? this.personalFinanceTaxonomyVersion
      : null;
    const date = new Date(transaction.date);

    await this.prisma.transaction.upsert({
      where: {
        plaidTransactionId: transaction.transaction_id,
      },
      create: {
        userId,
        accountId: account.id,
        plaidTransactionId: transaction.transaction_id,
        amount: new Prisma.Decimal(transaction.amount),
        name: transaction.name,
        merchantName: transaction.merchant_name ?? null,
        pending: transaction.pending,
        categoryPrimary: primaryCategory,
        categoryDetailed: detailedCategory,
        categoryConfidenceLevel: confidenceLevel,
        categoryTaxonomyVersion: taxonomyVersion,
        isoCurrencyCode: transaction.iso_currency_code ?? null,
        date,
      },
      update: {
        amount: new Prisma.Decimal(transaction.amount),
        name: transaction.name,
        merchantName: transaction.merchant_name ?? null,
        pending: transaction.pending,
        categoryPrimary: primaryCategory,
        categoryDetailed: detailedCategory,
        categoryConfidenceLevel: confidenceLevel,
        categoryTaxonomyVersion: taxonomyVersion,
        isoCurrencyCode: transaction.iso_currency_code ?? null,
        date,
      },
    });
  }
}
