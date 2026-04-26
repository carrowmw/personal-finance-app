import { Inject, Injectable } from "@nestjs/common";
import {
  DashboardSummary,
  TransactionListResponse,
} from "@personal-finances/contracts";

import { PrismaService } from "../common/prisma.service.js";

@Injectable()
export class FinanceService {
  constructor(@Inject(PrismaService) private readonly prisma: PrismaService) {}

  async getDashboardSummary(userId: string): Promise<DashboardSummary> {
    const now = new Date();
    const monthStart = new Date(
      Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1),
    );

    const transactions = await this.prisma.transaction.findMany({
      where: {
        userId,
        date: {
          gte: monthStart,
        },
      },
      select: {
        amount: true,
      },
    });

    let spendingMonth = 0;
    let incomeMonth = 0;

    for (const transaction of transactions) {
      const amount = Number(transaction.amount);
      if (amount >= 0) {
        spendingMonth += amount;
      } else {
        incomeMonth += Math.abs(amount);
      }
    }

    return {
      userId,
      netCashflowMonth: Number((incomeMonth - spendingMonth).toFixed(2)),
      spendingMonth: Number(spendingMonth.toFixed(2)),
      incomeMonth: Number(incomeMonth.toFixed(2)),
    };
  }

  async getRecentTransactions(
    userId: string,
  ): Promise<TransactionListResponse> {
    const transactions = await this.prisma.transaction.findMany({
      where: { userId },
      orderBy: { date: "desc" },
      take: 500,
      select: {
        id: true,
        date: true,
        amount: true,
        merchantName: true,
        name: true,
        categoryPrimary: true,
        categoryDetailed: true,
        categoryConfidenceLevel: true,
        categoryTaxonomyVersion: true,
      },
    });

    return {
      userId,
      transactions: transactions.map((transaction) => ({
        id: transaction.id,
        date: transaction.date.toISOString().slice(0, 10),
        amount: Number(transaction.amount),
        merchant: transaction.merchantName ?? transaction.name,
        personalFinanceCategoryPrimary: transaction.categoryPrimary,
        personalFinanceCategoryDetailed: transaction.categoryDetailed,
        personalFinanceCategoryConfidenceLevel:
          transaction.categoryConfidenceLevel,
        personalFinanceCategoryTaxonomyVersion:
          transaction.categoryTaxonomyVersion,
      })),
    };
  }
}
