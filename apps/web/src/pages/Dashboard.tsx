import { useState, useEffect } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Box,
  Container,
  Grid,
  Alert,
  CircularProgress,
} from "@mui/material";
import PersonIcon from "@mui/icons-material/Person";
import { usePlaidLink } from "react-plaid-link";

// Import API helpers and types
import { API_URL, requestJson } from "../utils/api";
import {
  DashboardSummary,
  TransactionListResponse,
  ManualSyncResponse,
} from "@personal-finances/contracts";

// We will import your UI panels from the components folder next!
import { DashboardPanel } from "../components/DashboardPanel";
import { ChartsPanel } from "../components/ChartsPanel";
import { TransactionsPanel } from "../components/TransactionsPanel";

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
  // UI State
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  // Data State
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [transactions, setTransactions] = useState<
    TransactionListResponse["transactions"]
  >([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Plaid State (for linking additional accounts)
  const [linkToken, setLinkToken] = useState<string | null>(null);

  // --- Data Fetching ---
  const fetchDashboard = async () => {
    const result = await requestJson<DashboardSummary>(
      `${API_URL}/finance/dashboard`,
      { headers: { Authorization: `Bearer ${token}` } },
      "loading dashboard",
    );
    setSummary(result);
  };

  const fetchTransactions = async () => {
    const result = await requestJson<TransactionListResponse>(
      `${API_URL}/finance/transactions`,
      { headers: { Authorization: `Bearer ${token}` } },
      "loading transactions",
    );
    setTransactions(result.transactions);
  };

  const refreshData = async () => {
    setIsRefreshing(true);
    setError(null);
    try {
      await Promise.all([fetchDashboard(), fetchTransactions()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data.");
    } finally {
      setIsRefreshing(false);
    }
  };

  // Initial load
  useEffect(() => {
    void refreshData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  // --- Menu Handlers ---
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) =>
    setAnchorEl(event.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);

  const handleLogout = () => {
    localStorage.removeItem("pf_token");
    setToken(null);
    setHasLinkedAccount(false);
  };

  const handleManualSync = async () => {
    handleMenuClose();
    setStatus("Running manual sync...");
    try {
      const payload = await requestJson<ManualSyncResponse>(
        `${API_URL}/sync/manual`,
        { method: "POST", headers: { Authorization: `Bearer ${token}` } },
        "running manual sync",
      );
      setStatus(
        `Sync complete. Processed ${payload.syncedTransactions} changes.`,
      );
      await refreshData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sync failed.");
    }
  };

  // --- Plaid Link (Additional Accounts) ---
  const { open: openPlaid } = usePlaidLink({
    token: linkToken,
    onSuccess: async (publicToken) => {
      setStatus("Linking new account...");
      try {
        await requestJson(
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

        // Poll for the new account's transactions
        setStatus(
          "Syncing new transactions... this usually takes 5-10 seconds.",
        );

        let syncedCount = 0;
        let attempts = 0;
        const maxAttempts = 4;

        // Give Plaid's extraction engine a 2-second head start
        await new Promise((resolve) => setTimeout(resolve, 2000));

        while (syncedCount === 0 && attempts < maxAttempts) {
          const syncPayload = await requestJson<{ syncedTransactions: number }>(
            `${API_URL}/sync/manual`,
            {
              method: "POST",
              headers: { Authorization: `Bearer ${token}` },
            },
            "running manual sync",
          );

          syncedCount = syncPayload.syncedTransactions;

          if (syncedCount > 0) {
            break; // Data arrived, exit immediately!
          }

          attempts++;
          if (attempts < maxAttempts) {
            await new Promise((resolve) => setTimeout(resolve, 2000));
          }
        }

        setStatus(`New account linked! Synced ${syncedCount} transactions.`);
        await refreshData();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to link account.",
        );
      }
    },
  });

  const handleLinkAnotherAccount = async () => {
    handleMenuClose();
    try {
      const payload = await requestJson<{ linkToken: string }>(
        `${API_URL}/plaid/create-link-token`,
        { method: "POST", headers: { Authorization: `Bearer ${token}` } },
        "creating Plaid link token",
      );
      setLinkToken(payload.linkToken);
      // Wait for React to update the linkToken state, then open Plaid
      setTimeout(() => openPlaid(), 100);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to initialize Plaid.",
      );
    }
  };

  return (
    <Box sx={{ flexGrow: 1, bgcolor: "#f9fafb", minHeight: "100vh" }}>
      {/* Top Navigation Bar */}
      <AppBar
        position="static"
        color="transparent"
        elevation={0}
        sx={{ borderBottom: "1px solid #e5e7eb", bgcolor: "white" }}
      >
        <Toolbar>
          <Typography
            variant="h6"
            component="div"
            sx={{ flexGrow: 1, fontWeight: "bold" }}
          >
            Personal Finances
          </Typography>

          <IconButton onClick={handleMenuOpen} color="inherit">
            <Avatar sx={{ bgcolor: "primary.main", width: 32, height: 32 }}>
              <PersonIcon />
            </Avatar>
          </IconButton>

          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            transformOrigin={{ horizontal: "right", vertical: "top" }}
            anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
          >
            <MenuItem onClick={handleManualSync}>Force Sync Data</MenuItem>
            <MenuItem onClick={handleLinkAnotherAccount}>
              Link Another Account
            </MenuItem>
            <MenuItem onClick={handleLogout} sx={{ color: "error.main" }}>
              Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      {/* Main Dashboard Content */}
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}
        {status && (
          <Alert severity="info" sx={{ mb: 3 }} onClose={() => setStatus(null)}>
            {status}
          </Alert>
        )}

        {isRefreshing && !summary ? (
          <Box sx={{ display: "flex", justifyContent: "center", mt: 10 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Grid container spacing={3}>
            {/* Note: These components will be extracted in the next step */}
            <Grid xs={12} md={4}>
              <DashboardPanel summary={summary} loading={isRefreshing} />
            </Grid>
            <Grid xs={12} md={8}>
              <ChartsPanel
                summary={summary}
                transactions={transactions}
                loading={isRefreshing}
              />
            </Grid>
            <Grid xs={12}>
              <TransactionsPanel
                transactions={transactions}
                loading={isRefreshing}
              />
            </Grid>
          </Grid>
        )}
      </Container>
    </Box>
  );
}
