import { Inject, Injectable, NotFoundException } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import { Prisma } from "@prisma/client";
import { TransactionsSyncRequest } from "plaid";

import { PrismaService } from "../common/prisma.service.js";
import { PlaidService } from "./plaid.service.js";
import { TokenEncryptionService } from "./token-encryption.service.js";

@Injectable()
export class TransactionSyncService {
  private readonly personalFinanceTaxonomyVersion: string | null;

  constructor(
    @Inject(ConfigService) private readonly configService: ConfigService,
    @Inject(PrismaService) private readonly prisma: PrismaService,
    @Inject(TokenEncryptionService)
    private readonly tokenEncryptionService: TokenEncryptionService,
    @Inject(PlaidService) private readonly plaidService: PlaidService,
  ) {
    this.personalFinanceTaxonomyVersion =
      this.configService.get<string>("PLAID_PFC_TAXONOMY_VERSION") ?? null;
  }

  async syncTransactions(userId: string): Promise<number> {
    const plaidClient = this.plaidService.getPlaidClient();

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
        access_token: this.tokenEncryptionService.decryptAccessToken(
          plaidItem.accessToken,
        ),
        cursor,
        count: 100,
      };

      try {
        const response = await plaidClient.transactionsSync(request);
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
}
