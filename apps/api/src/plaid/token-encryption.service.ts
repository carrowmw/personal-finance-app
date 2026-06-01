import { Inject, Injectable, ServiceUnavailableException } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import { createCipheriv, createDecipheriv, randomBytes } from "node:crypto";

import { PrismaService } from "../common/prisma.service.js";

@Injectable()
export class TokenEncryptionService {
  public static readonly ENCRYPTION_PREFIX = "enc:v1:";
  private readonly accessTokenKey: Buffer | null;

  constructor(
    @Inject(ConfigService) private readonly configService: ConfigService,
    @Inject(PrismaService) private readonly prisma: PrismaService,
  ) {
    const rawAccessTokenKey = this.configService.get<string>(
      "PLAID_ACCESS_TOKEN_ENCRYPTION_KEY",
    );
    this.accessTokenKey = rawAccessTokenKey
      ? Buffer.from(rawAccessTokenKey, "base64")
      : null;
  }

  encryptAccessToken(rawToken: string): string {
    const key = this.getAccessTokenKeyOrThrow();
    const iv = randomBytes(12);
    const cipher = createCipheriv("aes-256-gcm", key, iv);
    const encrypted = Buffer.concat([
      cipher.update(rawToken, "utf8"),
      cipher.final(),
    ]);
    const authTag = cipher.getAuthTag();
    return `${TokenEncryptionService.ENCRYPTION_PREFIX}${iv.toString("base64")}.${authTag.toString("base64")}.${encrypted.toString("base64")}`;
  }

  decryptAccessToken(storedValue: string): string {
    if (!storedValue.startsWith(TokenEncryptionService.ENCRYPTION_PREFIX)) {
      throw new ServiceUnavailableException(
        "Found legacy unencrypted Plaid token. Run the re-encryption maintenance task first.",
      );
    }

    const key = this.getAccessTokenKeyOrThrow();
    const payload = storedValue.slice(
      TokenEncryptionService.ENCRYPTION_PREFIX.length,
    );
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

  async reencryptLegacyAccessTokens(): Promise<{
    scanned: number;
    updated: number;
  }> {
    const legacyItems = await this.prisma.plaidItem.findMany({
      where: {
        NOT: {
          accessToken: {
            startsWith: TokenEncryptionService.ENCRYPTION_PREFIX,
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

  private getAccessTokenKeyOrThrow(): Buffer {
    if (!this.accessTokenKey || this.accessTokenKey.length !== 32) {
      throw new ServiceUnavailableException(
        "Invalid PLAID_ACCESS_TOKEN_ENCRYPTION_KEY. Expected a base64-encoded 32-byte key.",
      );
    }

    return this.accessTokenKey;
  }
}
