import { Controller, Get, Inject, Req, UseGuards } from "@nestjs/common";
import {
  DashboardSummary,
  TransactionListResponse,
} from "@personal-finances/contracts";

import { JwtAuthGuard } from "../auth/guards/jwt-auth.guard.js";
import { FinanceService } from "./finance.service.js";

@Controller("finance")
@UseGuards(JwtAuthGuard)
export class FinanceController {
  constructor(
    @Inject(FinanceService) private readonly financeService: FinanceService,
  ) {}

  @Get("dashboard")
  getDashboard(
    @Req() request: { user: { sub: string } },
  ): Promise<DashboardSummary> {
    return this.financeService.getDashboardSummary(request.user.sub);
  }

  @Get("transactions")
  getTransactions(
    @Req() request: { user: { sub: string } },
  ): Promise<TransactionListResponse> {
    return this.financeService.getRecentTransactions(request.user.sub);
  }
}
