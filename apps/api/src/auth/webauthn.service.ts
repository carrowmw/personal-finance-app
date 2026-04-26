import {
  BadRequestException,
  Inject,
  Injectable,
  ServiceUnavailableException,
} from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import {
  generateAuthenticationOptions,
  generateRegistrationOptions,
  verifyAuthenticationResponse,
  verifyRegistrationResponse,
} from "@simplewebauthn/server";
import type {
  AuthenticationResponseJSON,
  RegistrationResponseJSON,
} from "@simplewebauthn/types";

import { PrismaService } from "../common/prisma.service.js";

type WebAuthnConfig = {
  rpID: string;
  rpName: string;
  origins: string[];
};

@Injectable()
export class WebAuthnService {
  constructor(
    @Inject(ConfigService) private readonly configService: ConfigService,
    @Inject(PrismaService) private readonly prisma: PrismaService,
  ) {}

  async generateRegistrationOptionsForUser(userId: string): Promise<unknown> {
    const { rpID, rpName } = this.getWebAuthnConfig();

    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user) {
      throw new BadRequestException("Unknown user");
    }

    const existingCredentials = await this.prisma.webAuthnCredential.findMany({
      where: { userId },
      select: { credentialId: true, transports: true },
    });

    const userIDBytes = new TextEncoder().encode(user.id);

    const options = await generateRegistrationOptions({
      rpID,
      rpName,
      userID: userIDBytes,
      userName: user.email,
      attestationType: "none",
      authenticatorSelection: {
        userVerification: "required",
      },
      excludeCredentials: existingCredentials.map((cred) => ({
        id: cred.credentialId,
        transports: cred.transports
          ? (cred.transports.split(",").filter(Boolean) as any)
          : undefined,
      })),
    });

    await this.upsertChallenge(userId, "registration", options.challenge);

    return options;
  }

  async verifyRegistrationForUser(
    userId: string,
    response: RegistrationResponseJSON,
  ): Promise<void> {
    const config = this.getWebAuthnConfig();

    const expectedChallenge = await this.consumeChallenge(
      userId,
      "registration",
    );

    const verification = await verifyRegistrationResponse({
      response,
      expectedChallenge,
      expectedOrigin: config.origins,
      expectedRPID: config.rpID,
    });

    if (!verification.verified) {
      throw new BadRequestException(
        "Passkey registration could not be verified",
      );
    }

    const { credentialDeviceType, credentialBackedUp, credential } =
      verification.registrationInfo;

    const credentialId = credential.id;
    const publicKey = Buffer.from(credential.publicKey).toString("base64url");
    const transports = response.response.transports?.join(",");

    await this.prisma.webAuthnCredential.upsert({
      where: { credentialId },
      create: {
        userId,
        credentialId,
        publicKey,
        counter: credential.counter,
        transports,
        deviceType: credentialDeviceType,
        backedUp: credentialBackedUp,
      },
      update: {
        userId,
        publicKey,
        counter: credential.counter,
        transports,
        deviceType: credentialDeviceType,
        backedUp: credentialBackedUp,
      },
    });

    await this.prisma.user.update({
      where: { id: userId },
      data: { mfaEnabled: true },
    });
  }

  async generateAuthenticationOptionsForUser(userId: string): Promise<unknown> {
    const { rpID } = this.getWebAuthnConfig();

    const credentials = await this.prisma.webAuthnCredential.findMany({
      where: { userId },
      select: { credentialId: true, transports: true },
    });

    if (credentials.length === 0) {
      throw new BadRequestException("No passkey is registered for this user");
    }

    const options = await generateAuthenticationOptions({
      rpID,
      userVerification: "required",
      allowCredentials: credentials.map((cred) => ({
        id: cred.credentialId,
        transports: cred.transports
          ? (cred.transports.split(",").filter(Boolean) as any)
          : undefined,
      })),
    });

    await this.upsertChallenge(userId, "authentication", options.challenge);

    return options;
  }

  async verifyAuthenticationForUser(
    userId: string,
    response: AuthenticationResponseJSON,
  ): Promise<void> {
    const config = this.getWebAuthnConfig();

    const expectedChallenge = await this.consumeChallenge(
      userId,
      "authentication",
    );

    const credentialIdFromResponse = response.id;
    const credential = await this.prisma.webAuthnCredential.findUnique({
      where: { credentialId: credentialIdFromResponse },
    });

    if (!credential || credential.userId !== userId) {
      throw new BadRequestException("Unknown credential");
    }

    const verification = await verifyAuthenticationResponse({
      response,
      expectedChallenge,
      expectedOrigin: config.origins,
      expectedRPID: config.rpID,
      credential: {
        id: credential.credentialId,
        publicKey: Buffer.from(credential.publicKey, "base64url"),
        counter: credential.counter,
        transports: credential.transports
          ? (credential.transports.split(",").filter(Boolean) as any)
          : undefined,
      },
    });

    if (!verification.verified) {
      throw new BadRequestException("Passkey verification failed");
    }

    await this.prisma.webAuthnCredential.update({
      where: { credentialId: credential.credentialId },
      data: {
        counter: verification.authenticationInfo.newCounter,
      },
    });
  }

  private getWebAuthnConfig(): WebAuthnConfig {
    const rpName =
      this.configService.get<string>("WEBAUTHN_RP_NAME") ?? "Personal Finances";

    const originsRaw =
      this.configService.get<string>("WEBAUTHN_ORIGINS") ??
      this.configService.get<string>("CORS_ORIGINS") ??
      "";

    const origins = originsRaw
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean);

    if (origins.length === 0) {
      throw new ServiceUnavailableException(
        "Missing WEBAUTHN_ORIGINS (or CORS_ORIGINS) configuration",
      );
    }

    const derivedRpId = (() => {
      try {
        return new URL(origins[0]).hostname;
      } catch {
        return undefined;
      }
    })();

    const rpID =
      this.configService.get<string>("WEBAUTHN_RP_ID") ?? derivedRpId;

    if (!rpID) {
      throw new ServiceUnavailableException("Missing WEBAUTHN_RP_ID");
    }

    return { rpID, rpName, origins };
  }

  private async upsertChallenge(
    userId: string,
    type: "registration" | "authentication",
    challenge: string,
  ): Promise<void> {
    const expiresAt = new Date(Date.now() + 5 * 60 * 1000);

    await this.prisma.webAuthnChallenge.create({
      data: {
        userId,
        type,
        challenge,
        expiresAt,
      },
    });
  }

  private async consumeChallenge(
    userId: string,
    type: "registration" | "authentication",
  ): Promise<string> {
    const now = new Date();

    const record = await this.prisma.webAuthnChallenge.findFirst({
      where: {
        userId,
        type,
        expiresAt: { gt: now },
      },
      orderBy: { createdAt: "desc" },
    });

    if (!record) {
      throw new BadRequestException(
        "No active passkey challenge found. Please try again.",
      );
    }

    await this.prisma.webAuthnChallenge.delete({ where: { id: record.id } });

    return record.challenge;
  }
}
