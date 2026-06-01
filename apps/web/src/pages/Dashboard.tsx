import { useEffect } from "react";
import { Container, Grid, Alert } from "@mui/material";

import { useDashboardData } from "../hooks/useDashboardData";
import { usePlaidLinkFlow } from "../hooks/usePlaidLinkFlow";

import { DashboardLayout } from "../components/DashboardLayout";
import { DashboardPanel } from "../components/DashboardPanel";
import { ChartsPanel } from "../components/ChartsPanel";
import { TransactionsPanel } from "../components/TransactionsPanel";
import { CategoryPiePanel } from "../components/CategoryPiePanel";

interface DashboardProps {
  token: string;
  setToken: (token: string | null) => void;
  setHasLinkedAccount: (val: boolean) => void;
}

export function Dashboard({
  token,
  setToken,
  setHasLinkedAccount,
}: DashboardProps) {
  const {
    summary,
    transactions,
    loading,
    error: dashboardError,
    setError: setDashboardError,
    refreshData,
    runManualSync,
  } = useDashboardData(token);

  const {
    initiateLinkFlow,
    openPlaid,
    error: linkError,
    setError: setLinkError,
    statusMessage,
    setStatusMessage,
    linkToken,
  } = usePlaidLinkFlow(token, refreshData);

  useEffect(() => {
    void refreshData();
  }, [refreshData]);

  // Open Plaid automatically when the link token becomes available
  useEffect(() => {
    if (linkToken) {
      setTimeout(() => openPlaid(), 100);
    }
  }, [linkToken, openPlaid]);

  const handleLogout = () => {
    localStorage.removeItem("pf_token");
    setToken(null);
    setHasLinkedAccount(false);
  };

  const handleManualSync = async () => {
    setStatusMessage("Running manual sync...");
    try {
      const res = await runManualSync();
      setStatusMessage(
        `Sync complete. Processed ${res.syncedTransactions} changes.`,
      );
    } catch (err) {
      setDashboardError(err instanceof Error ? err.message : "Sync failed.");
    }
  };

  const handleLinkAnotherAccount = async () => {
    setLinkError(null);
    setDashboardError(null);
    setStatusMessage(null);
    await initiateLinkFlow();
  };

  return (
    <DashboardLayout
      onLogout={handleLogout}
      onManualSync={handleManualSync}
      onLinkAnotherAccount={handleLinkAnotherAccount}
    >
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {(dashboardError || linkError) && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {dashboardError || linkError}
          </Alert>
        )}
        {statusMessage && (
          <Alert
            severity="info"
            sx={{ mb: 3 }}
            onClose={() => setStatusMessage(null)}
          >
            {statusMessage}
          </Alert>
        )}

        {/* Row 1: 4 Cards */}
        <DashboardPanel summary={summary} loading={loading} />

        {/* Row 2: 2 Side-by-Side Charts */}
        <ChartsPanel transactions={transactions} loading={loading} />

        {/* Row 3: 3/4 Table, 1/4 Pie Chart */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={9}>
            <TransactionsPanel transactions={transactions} loading={loading} />
          </Grid>
          <Grid item xs={12} md={3}>
            <CategoryPiePanel transactions={transactions} loading={loading} />
          </Grid>
        </Grid>
      </Container>
    </DashboardLayout>
  );
}
