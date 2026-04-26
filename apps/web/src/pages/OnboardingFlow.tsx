import { useState, useEffect } from "react";
import {
  Container,
  Typography,
  Button,
  Box,
  Alert,
  CircularProgress,
} from "@mui/material";
import { usePlaidLink } from "react-plaid-link";

// Import API helpers
import { API_URL, requestJson } from "../utils/api";

interface OnboardingFlowProps {
  token: string;
  setHasLinkedAccount: (val: boolean) => void;
}

export function OnboardingFlow({
  token,
  setHasLinkedAccount,
}: OnboardingFlowProps) {
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null); // <-- Added status state
  const [isInitializing, setIsInitializing] = useState(true);
  const [isExchanging, setIsExchanging] = useState(false);

  // 1. Fetch the Link Token
  useEffect(() => {
    const fetchLinkToken = async () => {
      try {
        const payload = await requestJson<{ linkToken: string }>(
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
        setLinkToken(payload.linkToken);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to initialize Plaid.",
        );
      } finally {
        setIsInitializing(false);
      }
    };

    void fetchLinkToken();
  }, [token]);

  // 2. Configure Plaid Link
  const { open, ready } = usePlaidLink({
    token: linkToken,
    onSuccess: async (publicToken) => {
      setIsExchanging(true);
      setError(null);
      try {
        setStatusMessage("Linking account securely...");

        // Step A: Exchange Token
        await requestJson<{ userId: string; linked: boolean }>(
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

        // Step B: Poll for initial transactions
        setStatusMessage(
          "Syncing your financial data... this usually takes 5-10 seconds.",
        );

        let syncedCount = 0;
        let attempts = 0;
        const maxAttempts = 4;

        // Give Plaid's extraction engine a 2-second head start before our first request
        await new Promise((resolve) => setTimeout(resolve, 2000));

        while (syncedCount === 0 && attempts < maxAttempts) {
          const syncPayload = await requestJson<{ syncedTransactions: number }>(
            `${API_URL}/sync/manual`,
            {
              method: "POST",
              headers: { Authorization: `Bearer ${token}` },
            },
            "syncing initial transactions",
          );

          syncedCount = syncPayload.syncedTransactions;

          if (syncedCount > 0) {
            break; // We got the data, exit immediately!
          }

          attempts++;
          if (attempts < maxAttempts) {
            // Wait 2 seconds before the next poll
            await new Promise((resolve) => setTimeout(resolve, 2000));
          }
        }

        // Step C: Trigger redirect
        setHasLinkedAccount(true);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to link account.",
        );
        setIsExchanging(false);
        setStatusMessage(null);
      }
    },
  });

  return (
    <Container maxWidth="sm" sx={{ mt: 15, textAlign: "center" }}>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        Let's get started.
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
        To generate your financial dashboard, you need to securely link your
        primary bank account.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3, textAlign: "left" }}>
          {error}
        </Alert>
      )}

      {statusMessage && !error && (
        <Alert severity="info" sx={{ mb: 3, textAlign: "left" }}>
          {statusMessage}
        </Alert>
      )}

      <Box sx={{ mt: 4 }}>
        {isInitializing ? (
          <CircularProgress size={24} />
        ) : (
          <Button
            variant="contained"
            size="large"
            onClick={() => open()}
            disabled={!ready || isExchanging}
            sx={{ px: 4, py: 1.5, borderRadius: 2 }}
          >
            {isExchanging ? "Connecting..." : "Connect Bank Account"}
          </Button>
        )}
      </Box>
    </Container>
  );
}
