import { Controller, Inject, Post, Req, UseGuards } from "@nestjs/common";

import { JwtAuthGuard } from "../auth/guards/jwt-auth.guard.js";
import { SyncService } from "./sync.service.js";

@Controller("sync")
@UseGuards(JwtAuthGuard)
export class SyncController {
  constructor(@Inject(SyncService) private readonly syncService: SyncService) {}

  @Post("manual")
  runManualSync(
    @Req() request: { user: { sub: string } },
  ): Promise<{ userId: string; status: string; syncedTransactions: number }> {
    return this.syncService.runManualSync(request.user.sub);
  }
}
