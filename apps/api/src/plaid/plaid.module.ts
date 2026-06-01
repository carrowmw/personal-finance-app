import { Module } from "@nestjs/common";

import { AuthModule } from "../auth/auth.module.js";
import { PlaidController } from "./plaid.controller.js";
import { PlaidService } from "./plaid.service.js";
import { TokenEncryptionService } from "./token-encryption.service.js";
import { TransactionSyncService } from "./transaction-sync.service.js";

@Module({
  imports: [AuthModule],
  controllers: [PlaidController],
  providers: [PlaidService, TokenEncryptionService, TransactionSyncService],
  exports: [PlaidService, TransactionSyncService],
})
export class PlaidModule {}
