import { Inject, Injectable } from "@nestjs/common";

import { PlaidService } from "../plaid/plaid.service.js";

@Injectable()
export class SyncService {
  constructor(
    @Inject(PlaidService) private readonly plaidService: PlaidService,
  ) {}

  async runManualSync(userId: string): Promise<{
    userId: string;
    status: string;
    syncedTransactions: number;
  }> {
    const syncedTransactions = await this.plaidService.syncTransactions(userId);

    return {
      userId,
      status: "ok",
      syncedTransactions,
    };
  }
}
