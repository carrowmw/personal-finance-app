import {
  Box,
  Paper,
  Tabs,
  Tab,
  TextField,
  Button,
  Typography,
  Container,
  Alert,
} from "@mui/material";
import { useState } from "react";
import {
  startAuthentication,
  startRegistration,
} from "@simplewebauthn/browser";

// Import from the utils file
import { API_URL, requestJson } from "../utils/api";
import { authApi } from "../api";

type AuthMode = "register" | "login";

export function AuthPortal({ setToken }: { setToken: (t: string) => void }) {
  const [tab, setTab] = useState(0);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingMode, setLoadingMode] = useState<AuthMode | null>(null);

  const withAuthHeader = (currentToken: string): HeadersInit => ({
    "Content-Type": "application/json",
    Authorization: `Bearer ${currentToken}`,
  });

  const completeMfa = async (
    stage: "setup" | "authenticate",
    mfaToken: string,
  ) => {
    if (stage === "setup") {
      setStatus("Setting up passkey (security key/biometrics)...");
      const options = await requestJson<any>(
        `${API_URL}/auth/webauthn/register/options`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${mfaToken}` },
        },
        "creating passkey registration options",
      );

      const registrationResponse = await startRegistration(options);

      const verify = await requestJson<{ token: string }>(
        `${API_URL}/auth/webauthn/register/verify`,
        {
          method: "POST",
          headers: withAuthHeader(mfaToken),
          body: JSON.stringify({ response: registrationResponse }),
        },
        "verifying passkey registration",
      );

      localStorage.setItem("pf_token", verify.token);
      setToken(verify.token);
      return;
    }

    setStatus("Verifying passkey (security key/biometrics)...");
    const options = await requestJson<any>(
      `${API_URL}/auth/webauthn/authenticate/options`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${mfaToken}` },
      },
      "creating passkey authentication options",
    );

    const authenticationResponse = await startAuthentication(options);

    const verify = await requestJson<{ token: string }>(
      `${API_URL}/auth/webauthn/authenticate/verify`,
      {
        method: "POST",
        headers: withAuthHeader(mfaToken),
        body: JSON.stringify({ response: authenticationResponse }),
      },
      "verifying passkey authentication",
    );

    localStorage.setItem("pf_token", verify.token);
    setToken(verify.token);
  };

  const auth = async (mode: AuthMode) => {
    setLoadingMode(mode);
    setStatus("Working...");
    setError(null);

      const payload = await (mode === "login"
        ? authApi.login(email, password)
        : authApi.register(email, password));

      if (payload.token) {
        localStorage.setItem("pf_token", payload.token);
        setToken(payload.token);
        return;
      }

      if (payload.mfaRequired && payload.mfaToken && payload.mfaStage) {
        await completeMfa(payload.mfaStage, payload.mfaToken);
        setError(null);
        return;
      }

      throw new Error(
        "Authentication incomplete. MFA may be required but could not be initiated.",
      );
    } catch (err) {
      setStatus(null);
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoadingMode(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const mode = tab === 0 ? "login" : "register";
    await auth(mode);
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 10 }}>
      <Paper elevation={3} sx={{ borderRadius: 3, overflow: "hidden" }}>
        <Tabs
          value={tab}
          onChange={(_, newValue) => {
            setTab(newValue);
            setError(null);
            setStatus(null);
          }}
          variant="fullWidth"
        >
          <Tab label="Login" />
          <Tab label="Register" />
        </Tabs>

        <Box component="form" onSubmit={handleSubmit} sx={{ p: 4 }}>
          <Typography variant="h5" align="center" gutterBottom>
            {tab === 0 ? "Welcome Back" : "Create an Account"}
          </Typography>

          {/* Feedback Alerts */}
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          {status && !error && (
            <Alert severity="info" sx={{ mb: 2 }}>
              {status}
            </Alert>
          )}

          <TextField
            fullWidth
            margin="normal"
            label="Email"
            variant="outlined"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loadingMode !== null}
            required
          />
          <TextField
            fullWidth
            margin="normal"
            label="Password"
            type="password"
            variant="outlined"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loadingMode !== null}
            required
            autoComplete="current-password"
          />

          <Button
            fullWidth
            variant="contained"
            size="large"
            type="submit"
            disabled={loadingMode !== null}
            sx={{ mt: 3, py: 1.5 }}
          >
            {loadingMode !== null
              ? tab === 0
                ? "Logging in..."
                : "Registering..."
              : tab === 0
                ? "Login"
                : "Register"}
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}
