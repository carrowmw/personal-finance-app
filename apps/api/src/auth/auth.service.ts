import { Inject, Injectable, UnauthorizedException } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import { JwtService } from "@nestjs/jwt";
import { User } from "@prisma/client";
import bcrypt from "bcryptjs";

import { PrismaService } from "../common/prisma.service.js";

@Injectable()
export class AuthService {
  constructor(
    @Inject(PrismaService) private readonly prisma: PrismaService,
    @Inject(JwtService) private readonly jwtService: JwtService,
    @Inject(ConfigService) private readonly configService: ConfigService,
  ) {}

  async register(
    email: string,
    password: string,
  ): Promise<{
    token?: string;
    mfaRequired: boolean;
    mfaStage?: "setup" | "authenticate";
    mfaToken?: string;
    user: { id: string; email: string };
  }> {
    const existing = await this.prisma.user.findUnique({ where: { email } });
    if (existing) {
      throw new UnauthorizedException("Email is already registered");
    }

    const passwordHash = await bcrypt.hash(password, 12);
    const user = await this.prisma.user.create({
      data: {
        email,
        passwordHash,
      },
    });

    if (this.isMfaRequired()) {
      return {
        mfaRequired: true,
        mfaStage: "setup",
        mfaToken: this.signMfaToken(user, "setup"),
        user: { id: user.id, email: user.email },
      };
    }

    return {
      token: this.signAccessToken(user),
      mfaRequired: false,
      user: {
        id: user.id,
        email: user.email,
      },
    };
  }

  async login(
    email: string,
    password: string,
  ): Promise<{
    token?: string;
    mfaRequired: boolean;
    mfaStage?: "setup" | "authenticate";
    mfaToken?: string;
    user: { id: string; email: string };
  }> {
    const user = await this.prisma.user.findUnique({ where: { email } });
    if (!user) {
      throw new UnauthorizedException("Invalid credentials");
    }

    const isValid = await bcrypt.compare(password, user.passwordHash);
    if (!isValid) {
      throw new UnauthorizedException("Invalid credentials");
    }

    if (this.isMfaRequired()) {
      const hasPasskey =
        user.mfaEnabled ||
        (await this.prisma.webAuthnCredential.count({
          where: { userId: user.id },
        })) > 0;

      if (!hasPasskey) {
        return {
          mfaRequired: true,
          mfaStage: "setup",
          mfaToken: this.signMfaToken(user, "setup"),
          user: { id: user.id, email: user.email },
        };
      }

      return {
        mfaRequired: true,
        mfaStage: "authenticate",
        mfaToken: this.signMfaToken(user, "authenticate"),
        user: { id: user.id, email: user.email },
      };
    }

    return {
      token: this.signAccessToken(user),
      mfaRequired: false,
      user: {
        id: user.id,
        email: user.email,
      },
    };
  }

  async issueAccessTokenForUser(userId: string): Promise<string> {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user) {
      throw new UnauthorizedException("User not found");
    }

    return this.signAccessToken(user);
  }

  async me(userId: string): Promise<{ id: string; email: string }> {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user) {
      throw new UnauthorizedException("User not found");
    }

    return {
      id: user.id,
      email: user.email,
    };
  }

  private signAccessToken(user: User): string {
    return this.jwtService.sign({
      sub: user.id,
      email: user.email,
      mfa: "verified",
    });
  }

  private signMfaToken(user: User, stage: "setup" | "authenticate"): string {
    return this.jwtService.sign(
      { sub: user.id, email: user.email, mfa: stage },
      { expiresIn: "10m" },
    );
  }

  private isMfaRequired(): boolean {
    return this.configService.get<boolean>("MFA_REQUIRED") ?? false;
  }
}
