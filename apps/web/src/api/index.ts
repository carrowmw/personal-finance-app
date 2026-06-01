import {
  AuthResponse,
  DashboardSummary,
  ManualSyncResponse,
  PlaidExchangeResponse,
  PlaidLinkTokenResponse,
  TransactionListResponse,
  UserMeResponse,
} from "@personal-finances/contracts";
import { API_URL, requestJson } from "../utils/api";

export const authApi = {
  register: (email: string, password: string): Promise<AuthResponse> => {
    return requestJson<AuthResponse>(
      `${API_URL}/auth/register`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      },
      "registering account",
    );
  },

  login: (email: string, password: string): Promise<AuthResponse> => {
    return requestJson<AuthResponse>(
      `${API_URL}/auth/login`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      },
      "logging in",
    );
  },

  me: (token: string): Promise<UserMeResponse> => {
    return requestJson<UserMeResponse>(
      `${API_URL}/auth/me`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${token}` },
      },
      "fetching user profile",
    );
  },
};

export const financeApi = {
  getDashboard: (token: string): Promise<DashboardSummary> => {
    return requestJson<DashboardSummary>(
      `${API_URL}/finance/dashboard`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${token}` },
      },
      "fetching dashboard summary",
    );
  },

  getTransactions: (token: string): Promise<TransactionListResponse> => {
    return requestJson<TransactionListResponse>(
      `${API_URL}/finance/transactions`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${token}` },
      },
      "fetching recent transactions",
    );
  },
};

export const syncApi = {
  runManualSync: (token: string): Promise<ManualSyncResponse> => {
    return requestJson<ManualSyncResponse>(
      `${API_URL}/sync/manual`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      },
      "syncing transactions",
    );
  },
};

export const plaidApi = {
  createLinkToken: (token: string): Promise<PlaidLinkTokenResponse> => {
    return requestJson<PlaidLinkTokenResponse>(
      `${API_URL}/plaid/create-link-token`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      },
      "creating Plaid link token",
    );
  },

  exchangeToken: (
    token: string,
    publicToken: string,
  ): Promise<PlaidExchangeResponse> => {
    return requestJson<PlaidExchangeResponse>(
      `${API_URL}/plaid/exchange-token`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ publicToken }),
      },
      "linking account",
    );
  },
};
