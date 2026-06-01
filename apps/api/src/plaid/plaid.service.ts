import {
  BadRequestException,
  Inject,
  Injectable,
  ServiceUnavailableException,
} from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import {
  Configuration,
  CountryCode,
  PlaidApi,
  PlaidEnvironments,
  Products,
} from "plaid";

import { PrismaService } from "../common/prisma.service.js";
import { TokenEncryptionService } from "./token-encryption.service.js";

@Injectable()
export class PlaidService {
  private readonly plaidClient: PlaidApi;
  private readonly plaidClientId: string | undefined;
  private readonly plaidSecret: string | undefined;
  private readonly products: Products[];
  private readonly countryCodes: CountryCode[];
  private readonly plaidRedirectUri: string | null;

  constructor(
    @Inject(ConfigService) private readonly configService: ConfigService,
    @Inject(PrismaService) private readonly prisma: PrismaService,
    @Inject(TokenEncryptionService)
    private readonly tokenEncryptionService: TokenEncryptionService,
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

    this.plaidRedirectUri =
      this.configService.get<string>("PLAID_REDIRECT_URI") ?? null;

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

  getPlaidClient(): PlaidApi {
    this.ensurePlaidConfigured();
    return this.plaidClient;
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
        accessToken: this.tokenEncryptionService.encryptAccessToken(
          exchangeResponse.data.access_token,
        ),
      },
      update: {
        userId,
        accessToken: this.tokenEncryptionService.encryptAccessToken(
          exchangeResponse.data.access_token,
        ),
      },
    });

    return {
      userId,
      linked: true,
    };
  }

  async reencryptLegacyAccessTokens(): Promise<{
    scanned: number;
    updated: number;
  }> {
    return this.tokenEncryptionService.reencryptLegacyAccessTokens();
  }

  private ensurePlaidConfigured(): void {
    if (!this.plaidClientId || !this.plaidSecret) {
      throw new ServiceUnavailableException("Missing Plaid credentials");
    }
  }

  private async ensureUserExists(userId: string): Promise<void> {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user) {
      throw new BadRequestException("Unknown user");
    }
  }
}
