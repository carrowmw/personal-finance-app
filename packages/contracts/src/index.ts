export type UserId = string;

export type AuthResponse = {
  token?: string;
  mfaRequired: boolean;
  mfaStage?: "setup" | "authenticate";
  mfaToken?: string;
  user: { id: string; email: string };
};

export type ApiErrorPayload = {
  message?: string | string[];
  error?: string;
  statusCode?: number;
};

export type PlaidLinkTokenResponse = {
  linkToken: string;
};

export type PlaidExchangeResponse = {
  userId: string;
  linked: boolean;
};

export type UserMeResponse = {
  id: string;
  email: string;
  hasLinkedAccount: boolean;
};

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
