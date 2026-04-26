import { Module } from "@nestjs/common";

import { AuthModule } from "../auth/auth.module.js";
import { PlaidController } from "./plaid.controller.js";
import { PlaidService } from "./plaid.service.js";

@Module({
  imports: [AuthModule],
  controllers: [PlaidController],
  providers: [PlaidService],
  exports: [PlaidService],
})
export class PlaidModule {}
