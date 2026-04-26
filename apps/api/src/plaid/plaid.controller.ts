import {
  BadRequestException,
  Body,
  Controller,
  ForbiddenException,
  Headers,
  Inject,
  Post,
  Req,
  UseGuards,
} from "@nestjs/common";
import { IsString } from "class-validator";
import { ConfigService } from "@nestjs/config";

import { JwtAuthGuard } from "../auth/guards/jwt-auth.guard.js";
import { PlaidService } from "./plaid.service.js";

class ExchangePublicTokenDto {
  @IsString()
  publicToken!: string;
}

@Controller("plaid")
@UseGuards(JwtAuthGuard)
export class PlaidController {
  constructor(
    @Inject(ConfigService) private readonly configService: ConfigService,
    @Inject(PlaidService) private readonly plaidService: PlaidService,
  ) {}

  @Post("exchange-token")
  exchangeToken(
    @Req() request: { user: { sub: string } },
    @Body() payload: ExchangePublicTokenDto,
  ): Promise<{
    userId: string;
    linked: boolean;
  }> {
    return this.plaidService.exchangePublicToken(
      request.user.sub,
      payload.publicToken,
    );
  }

  @Post("create-link-token")
  createLinkToken(
    @Req() request: { user: { sub: string } },
  ): Promise<{ linkToken: string }> {
    return this.plaidService.createLinkToken(request.user.sub);
  }

  @Post("admin/reencrypt-legacy-tokens")
  async reencryptLegacyTokens(
    @Headers("x-maintenance-key") maintenanceKey: string | undefined,
  ): Promise<{ scanned: number; updated: number }> {
    const expectedKey = this.configService.get<string>(
      "PLAID_TOKEN_MAINTENANCE_KEY",
    );

    if (!expectedKey) {
      throw new BadRequestException(
        "PLAID_TOKEN_MAINTENANCE_KEY is not configured",
      );
    }

    if (!maintenanceKey || maintenanceKey !== expectedKey) {
      throw new ForbiddenException("Invalid maintenance key");
    }

    return this.plaidService.reencryptLegacyAccessTokens();
  }
}
