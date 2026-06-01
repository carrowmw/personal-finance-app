import { useState, useCallback, useEffect } from "react";
import { usePlaidLink } from "react-plaid-link";
import { plaidApi, syncApi } from "../api";

export function usePlaidLinkFlow(
  token: string | null,
  onSuccessCallback?: () => void,
) {
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [isExchanging, setIsExchanging] = useState(false);

  const initiateLinkFlow = useCallback(async () => {
    if (!token) return;
    setIsInitializing(true);
    setError(null);
    try {
      const { linkToken } = await plaidApi.createLinkToken(token);
      setLinkToken(linkToken);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to initialize Plaid.",
      );
    } finally {
      setIsInitializing(false);
    }
  }, [token]);

  const { open, ready } = usePlaidLink({
    token: linkToken,
    onSuccess: async (publicToken) => {
      if (!token) return;
      setIsExchanging(true);
      setError(null);
      try {
        setStatusMessage("Linking account securely...");
        await plaidApi.exchangeToken(token, publicToken);

        setStatusMessage(
          "Syncing your financial data... this usually takes 5-10 seconds.",
        );

        let syncedCount = 0;
        let attempts = 0;
        const maxAttempts = 4;

        await new Promise((resolve) => setTimeout(resolve, 2000));

        while (syncedCount === 0 && attempts < maxAttempts) {
          const syncPayload = await syncApi.runManualSync(token);
          syncedCount = syncPayload.syncedTransactions;

          if (syncedCount > 0) break;

          attempts++;
          if (attempts < maxAttempts) {
            await new Promise((resolve) => setTimeout(resolve, 2000));
          }
        }

        setStatusMessage(
          `Account linked successfully! Synced ${syncedCount} transactions.`,
        );
        if (onSuccessCallback) {
          onSuccessCallback();
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to link account.",
        );
      } finally {
        setIsExchanging(false);
      }
    },
  });

  const openPlaid = useCallback(() => {
    if (ready) {
      open();
    }
  }, [ready, open]);

  // When linkToken changes, automatically open if ready and requested
  // It's cleaner to let the consumer call initiateLinkFlow, and then openPlaid when ready,
  // but react-plaid-link doesn't open until we call open() with the token.

  return {
    linkToken,
    initiateLinkFlow,
    openPlaid,
    ready,
    isInitializing,
    isExchanging,
    error,
    setError,
    statusMessage,
    setStatusMessage,
  };
}
