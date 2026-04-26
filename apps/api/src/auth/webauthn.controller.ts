import { Body, Controller, Inject, Post, Req, UseGuards } from "@nestjs/common";
import { IsObject } from "class-validator";

import { JwtPreAuthGuard } from "./guards/jwt-preauth.guard.js";
import { AuthService } from "./auth.service.js";
import { WebAuthnService } from "./webauthn.service.js";

class VerifyPayloadDto {
  @IsObject()
  response!: Record<string, unknown>;
}

@Controller("auth/webauthn")
@UseGuards(JwtPreAuthGuard)
export class WebAuthnController {
  constructor(
    @Inject(WebAuthnService) private readonly webAuthnService: WebAuthnService,
    @Inject(AuthService) private readonly authService: AuthService,
  ) {}

  @Post("register/options")
  async registrationOptions(
    @Req() request: { user: { sub: string } },
  ): Promise<unknown> {
    return this.webAuthnService.generateRegistrationOptionsForUser(
      request.user.sub,
    );
  }

  @Post("register/verify")
  async verifyRegistration(
    @Req() request: { user: { sub: string } },
    @Body() payload: VerifyPayloadDto,
  ): Promise<{ token: string }> {
    await this.webAuthnService.verifyRegistrationForUser(
      request.user.sub,
      payload.response as any,
    );

    const token = await this.authService.issueAccessTokenForUser(
      request.user.sub,
    );

    return { token };
  }

  @Post("authenticate/options")
  async authenticationOptions(
    @Req() request: { user: { sub: string } },
  ): Promise<unknown> {
    return this.webAuthnService.generateAuthenticationOptionsForUser(
      request.user.sub,
    );
  }

  @Post("authenticate/verify")
  async verifyAuthentication(
    @Req() request: { user: { sub: string } },
    @Body() payload: VerifyPayloadDto,
  ): Promise<{ token: string }> {
    await this.webAuthnService.verifyAuthenticationForUser(
      request.user.sub,
      payload.response as any,
    );

    const token = await this.authService.issueAccessTokenForUser(
      request.user.sub,
    );

    return { token };
  }
}
