import { Controller, Get, Inject, Req, UseGuards } from "@nestjs/common";

import { JwtAuthGuard } from "../auth/guards/jwt-auth.guard.js";
import { FinanceService } from "./finance.service.js";

@Controller("finance")
@UseGuards(JwtAuthGuard)
export class FinanceController {
  constructor(
    @Inject(FinanceService) private readonly financeService: FinanceService,
  ) {}

  @Get("dashboard")
  getDashboard(@Req() request: { user: { sub: string } }): Promise<{
    userId: string;
    netCashflowMonth: number;
    spendingMonth: number;
    incomeMonth: number;
  }> {
    return this.financeService.getDashboardSummary(request.user.sub);
  }

  @Get("transactions")
  getTransactions(@Req() request: { user: { sub: string } }): Promise<{
    userId: string;
    transactions: Array<{
      id: string;
      date: string;
      amount: number;
      merchant: string;
    }>;
  }> {
    return this.financeService.getRecentTransactions(request.user.sub);
  }
}
