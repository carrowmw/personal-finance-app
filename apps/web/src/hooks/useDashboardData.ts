import { useState, useCallback } from "react";
import { financeApi, syncApi } from "../api";
import {
  DashboardSummary,
  TransactionRecord,
} from "@personal-finances/contracts";

export function useDashboardData(token: string | null) {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [transactions, setTransactions] = useState<TransactionRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshData = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [dashRes, transRes] = await Promise.all([
        financeApi.getDashboard(token),
        financeApi.getTransactions(token),
      ]);
      setSummary(dashRes);
      setTransactions(transRes.transactions);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  const runManualSync = useCallback(async () => {
    if (!token) return { syncedTransactions: 0 };
    const res = await syncApi.runManualSync(token);
    await refreshData();
    return res;
  }, [token, refreshData]);

  return {
    summary,
    transactions,
    loading,
    error,
    setError,
    refreshData,
    runManualSync,
  };
}
