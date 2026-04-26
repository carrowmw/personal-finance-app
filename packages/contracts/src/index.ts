export type UserId = string;

export type DashboardSummary = {
  userId: UserId;
  netCashflowMonth: number;
  spendingMonth: number;
  incomeMonth: number;
};

export type TransactionRecord = {
  id: string;
  date: string;
  amount: number;
  merchant: string;
  personalFinanceCategoryPrimary?: string | null;
  personalFinanceCategoryDetailed?: string | null;
  personalFinanceCategoryConfidenceLevel?: string | null;
  personalFinanceCategoryTaxonomyVersion?: string | null;
};

export type TransactionListResponse = {
  userId: UserId;
  transactions: TransactionRecord[];
};

export type ManualSyncResponse = {
  userId: UserId;
  status: "ok" | "error";
  syncedTransactions: number;
};
