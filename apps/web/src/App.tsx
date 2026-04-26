import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { AuthPortal } from "./pages/AuthPortal";
import { OnboardingFlow } from "./pages/OnboardingFlow";
import { Dashboard } from "./pages/Dashboard";
import { API_URL, requestJson } from "./utils/api";

export function App() {
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("pf_token"),
  );
  const [hasLinkedAccount, setHasLinkedAccount] = useState<boolean | null>(
    null,
  );

  // When the app loads or token changes, verify token validity and linked account status
  useEffect(() => {
    if (!token) {
      setHasLinkedAccount(null);
      return;
    }

    const checkLinkedStatus = async () => {
      try {
        const user = await requestJson<{ hasLinkedAccount: boolean }>(
          `${API_URL}/auth/me`,
          { headers: { Authorization: `Bearer ${token}` } },
          "checking user status",
        );
        setHasLinkedAccount(user.hasLinkedAccount);
      } catch {
        // If the /me request fails, the token is likely invalid/expired.
        localStorage.removeItem("pf_token");
        setToken(null);
        setHasLinkedAccount(false);
      }
    };

    void checkLinkedStatus();
  }, [token]);

  // Prevent routing flicker while checking status
  if (token && hasLinkedAccount === null) {
    return null;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            token ? (
              <Navigate
                to={hasLinkedAccount ? "/dashboard" : "/onboarding"}
                replace
              />
            ) : (
              <AuthPortal setToken={setToken} />
            )
          }
        />
        <Route
          path="/onboarding"
          element={
            !token ? (
              <Navigate to="/" replace />
            ) : hasLinkedAccount ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <OnboardingFlow
                token={token}
                setHasLinkedAccount={setHasLinkedAccount}
              />
            )
          }
        />
        <Route
          path="/dashboard"
          element={
            !token ? (
              <Navigate to="/" replace />
            ) : !hasLinkedAccount ? (
              <Navigate to="/onboarding" replace />
            ) : (
              <Dashboard
                token={token}
                setToken={setToken}
                setHasLinkedAccount={setHasLinkedAccount}
              />
            )
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
