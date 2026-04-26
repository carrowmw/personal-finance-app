import { Module } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import { JwtModule } from "@nestjs/jwt";
import { PassportModule } from "@nestjs/passport";

import { AuthController } from "./auth.controller.js";
import { AuthService } from "./auth.service.js";
import { JwtAuthGuard } from "./guards/jwt-auth.guard.js";
import { JwtPreAuthGuard } from "./guards/jwt-preauth.guard.js";
import { JwtStrategy } from "./strategies/jwt.strategy.js";
import { WebAuthnController } from "./webauthn.controller.js";
import { WebAuthnService } from "./webauthn.service.js";

@Module({
  imports: [
    PassportModule,
    JwtModule.registerAsync({
      inject: [ConfigService],
      useFactory: (configService: ConfigService) => ({
        secret: configService.getOrThrow<string>("JWT_SECRET"),
        signOptions: { expiresIn: "7d" },
      }),
    }),
  ],
  controllers: [AuthController, WebAuthnController],
  providers: [
    AuthService,
    JwtStrategy,
    JwtAuthGuard,
    JwtPreAuthGuard,
    WebAuthnService,
  ],
  exports: [
    AuthService,
    PassportModule,
    JwtAuthGuard,
    JwtPreAuthGuard,
    WebAuthnService,
  ],
})
export class AuthModule {}
