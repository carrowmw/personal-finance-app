import { useEffect } from "react";
import {
  Container,
  Typography,
  Button,
  Box,
  Alert,
  CircularProgress,
} from "@mui/material";

import { usePlaidLinkFlow } from "../hooks/usePlaidLinkFlow";

interface OnboardingFlowProps {
  token: string;
  setHasLinkedAccount: (val: boolean) => void;
}

export function OnboardingFlow({
  token,
  setHasLinkedAccount,
}: OnboardingFlowProps) {
  const {
    initiateLinkFlow,
    openPlaid,
    ready,
    isInitializing,
    isExchanging,
    error,
    statusMessage,
  } = usePlaidLinkFlow(token, () => setHasLinkedAccount(true));

  useEffect(() => {
    void initiateLinkFlow();
  }, [initiateLinkFlow]);

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
            onClick={() => openPlaid()}
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
