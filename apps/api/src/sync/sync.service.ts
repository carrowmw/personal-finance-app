import { Inject, Injectable } from "@nestjs/common";

import { TransactionSyncService } from "../plaid/transaction-sync.service.js";

@Injectable()
export class SyncService {
  constructor(
    @Inject(TransactionSyncService)
    private readonly transactionSyncService: TransactionSyncService,
  ) {}

  async runManualSync(userId: string): Promise<{
    userId: string;
    status: string;
    syncedTransactions: number;
  }> {
    const syncedTransactions =
      await this.transactionSyncService.syncTransactions(userId);

    return {
      userId,
      status: "ok",
      syncedTransactions,
    };
  }
}
