import { useEffect, useState } from "react";
import {
  DashboardSummary,
  ManualSyncResponse,
  TransactionRecord,
  TransactionListResponse,
} from "@personal-finances/contracts";
import {
  startAuthentication,
  startRegistration,
} from "@simplewebauthn/browser";
import { usePlaidLink } from "react-plaid-link";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:4000/api";

type AuthMode = "register" | "login";

type TrendPoint = {
  date: string;
  income: number;
  spending: number;
};

type DateRangeKey = "7d" | "30d" | "90d";
type FlowType = "income" | "spending";

type CategoryBreakdownEntry = {
  category: string;
  total: number;
  count: number;
  topDetailedCategory: string;
};

type ApiErrorPayload = {
  message?: string | string[];
  error?: string;
  statusCode?: number;
};

type AuthApiResponse = {
  token?: string;
  mfaRequired: boolean;
  mfaStage?: "setup" | "authenticate";
  mfaToken?: string;
  user: { id: string; email: string };
};

function normalizeApiMessage(payload: ApiErrorPayload | null): string | null {
  if (!payload?.message) {
    return null;
  }

  if (Array.isArray(payload.message)) {
    return payload.message.join("; ");
  }

  return payload.message;
}

function buildApiErrorMessage(
  context: string,
  status: number,
  payload: ApiErrorPayload | null,
): string {
  const apiMessage = normalizeApiMessage(payload);

  if (status === 401) {
    return (
      apiMessage ??
      "Session expired or invalid credentials. Please login again."
    );
  }

  if (status === 400) {
    return apiMessage ?? `Invalid request while ${context}.`;
  }

  if (status === 503) {
    return (
      apiMessage ??
      "Service is temporarily unavailable. Check API/Plaid configuration."
    );
  }

  if (status >= 500) {
    return apiMessage ?? `Server error while ${context}.`;
  }

  return apiMessage ?? `${context} failed (HTTP ${status}).`;
}

async function requestJson<T>(
  url: string,
  init: RequestInit,
  context: string,
): Promise<T> {
  const response = await fetch(url, init);

  let payload: ApiErrorPayload | null = null;
  try {
    payload = (await response.json()) as ApiErrorPayload;
  } catch {
    payload = null;
  }

  if (!response.ok) {
    throw new Error(buildApiErrorMessage(context, response.status, payload));
  }

  return payload as T;
}

function AuthSection(props: {
  email: string;
  password: string;
  disabled: boolean;
  authLoadingMode: AuthMode | null;
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onRegister: () => void;
  onLogin: () => void;
  onLogout: () => void;
}) {
  return (
    <section className="panel">
      <h2 className="panel-title">Authentication</h2>
      <div className="form-grid">
        <input
          value={props.email}
          onChange={(event) => props.onEmailChange(event.target.value)}
          placeholder="Email"
          disabled={props.disabled}
        />
        <input
          type="password"
          value={props.password}
          onChange={(event) => props.onPasswordChange(event.target.value)}
          placeholder="Password"
          disabled={props.disabled}
        />
        <div className="button-row">
          <button
            onClick={props.onRegister}
            disabled={props.disabled || props.authLoadingMode !== null}
          >
            {props.authLoadingMode === "register"
              ? "Registering..."
              : "Register"}
          </button>
          <button
            onClick={props.onLogin}
            disabled={props.disabled || props.authLoadingMode !== null}
          >
            {props.authLoadingMode === "login" ? "Logging in..." : "Login"}
          </button>
          <button onClick={props.onLogout} disabled={props.disabled}>
            Logout
          </button>
        </div>
      </div>
    </section>
  );
}

function PlaidActions(props: {
  disabled: boolean;
  linkTokenReady: boolean;
  plaidReady: boolean;
  creatingLinkToken: boolean;
  exchangingToken: boolean;
  syncing: boolean;
  onCreateLinkToken: () => void;
  onOpenPlaid: () => void;
  onRunManualSync: () => void;
}) {
  return (
    <section className="panel">
      <h2 className="panel-title">Bank Link & Sync</h2>
      <div className="button-row wrap">
        <button
          onClick={props.onCreateLinkToken}
          disabled={props.disabled || props.creatingLinkToken}
        >
          {props.creatingLinkToken ? "Creating..." : "Create Link Token"}
        </button>
        <button
          onClick={props.onOpenPlaid}
          disabled={
            props.disabled ||
            props.exchangingToken ||
            !props.linkTokenReady ||
            !props.plaidReady
          }
        >
          {props.exchangingToken ? "Linking..." : "Open Plaid Link"}
        </button>
        <button
          onClick={props.onRunManualSync}
          disabled={props.disabled || props.syncing}
        >
          {props.syncing ? "Syncing..." : "Run Manual Sync"}
        </button>
      </div>
    </section>
  );
}

function DashboardPanel(props: {
  summary: DashboardSummary | null;
  loading: boolean;
}) {
  return (
    <section className="panel">
      <h2 className="panel-title">Dashboard</h2>
      {props.summary ? (
        <ul className="metric-list">
          <li>
            Net cashflow (month): {props.summary.netCashflowMonth.toFixed(2)}
          </li>
          <li>Income (month): {props.summary.incomeMonth.toFixed(2)}</li>
          <li>Spending (month): {props.summary.spendingMonth.toFixed(2)}</li>
        </ul>
      ) : (
        <p>{props.loading ? "Loading summary..." : "No dashboard data yet."}</p>
      )}
    </section>
  );
}

function TransactionsPanel(props: {
  transactions: TransactionRecord[];
  loading: boolean;
}) {
  return (
    <section className="panel">
      <h2 className="panel-title">Recent Transactions</h2>
      {props.loading ? (
        <p>Loading transactions...</p>
      ) : props.transactions.length === 0 ? (
        <p>No transactions yet.</p>
      ) : (
        <table className="transactions-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Merchant</th>
              <th className="align-right">Amount</th>
            </tr>
          </thead>
          <tbody>
            {props.transactions.map((transaction) => (
              <tr key={transaction.id}>
                <td>{transaction.date}</td>
                <td>{transaction.merchant}</td>
                <td className="align-right">{transaction.amount.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

function getRangeDays(range: DateRangeKey): number {
  if (range === "7d") {
    return 7;
  }

  if (range === "90d") {
    return 90;
  }

  return 30;
}

function filterTransactionsByRange(
  transactions: TransactionRecord[],
  range: DateRangeKey,
): TransactionRecord[] {
  const days = getRangeDays(range);
  const start = new Date();
  start.setHours(0, 0, 0, 0);
  start.setDate(start.getDate() - (days - 1));

  return transactions.filter((transaction) => {
    const date = new Date(`${transaction.date}T00:00:00`);
    return date >= start;
  });
}

function buildTrendData(
  transactions: TransactionRecord[],
  maxPoints: number,
): TrendPoint[] {
  const grouped = new Map<string, TrendPoint>();

  for (const transaction of transactions) {
    const existing = grouped.get(transaction.date) ?? {
      date: transaction.date,
      income: 0,
      spending: 0,
    };

    if (transaction.amount < 0) {
      existing.income += Math.abs(transaction.amount);
    } else {
      existing.spending += transaction.amount;
    }

    grouped.set(transaction.date, existing);
  }

  return Array.from(grouped.values())
    .sort((first, second) => first.date.localeCompare(second.date))
    .slice(-maxPoints);
}

function buildCategoryBreakdown(
  transactions: TransactionRecord[],
  flowType: FlowType,
): CategoryBreakdownEntry[] {
  const grouped = new Map<
    string,
    {
      category: string;
      total: number;
      count: number;
      detailedTotals: Map<string, number>;
    }
  >();

  for (const transaction of transactions) {
    const isIncome = transaction.amount < 0;
    if (flowType === "income" && !isIncome) {
      continue;
    }

    if (flowType === "spending" && isIncome) {
      continue;
    }

    const category =
      transaction.personalFinanceCategoryPrimary ?? "Uncategorized";
    const detailedCategory =
      transaction.personalFinanceCategoryDetailed ?? "Unspecified";
    const amount = Math.abs(transaction.amount);
    const existing = grouped.get(category) ?? {
      category,
      total: 0,
      count: 0,
      detailedTotals: new Map<string, number>(),
    };

    existing.total += amount;
    existing.count += 1;
    existing.detailedTotals.set(
      detailedCategory,
      (existing.detailedTotals.get(detailedCategory) ?? 0) + amount,
    );
    grouped.set(category, existing);
  }

  return Array.from(grouped.values())
    .map((entry) => {
      const topDetailedCategory = Array.from(
        entry.detailedTotals.entries(),
      ).sort((first, second) => second[1] - first[1])[0]?.[0];

      return {
        category: entry.category,
        total: entry.total,
        count: entry.count,
        topDetailedCategory: topDetailedCategory ?? "Unspecified",
      };
    })
    .sort((first, second) => second.total - first.total)
    .slice(0, 8);
}

function ChartsPanel(props: {
  summary: DashboardSummary | null;
  transactions: TransactionRecord[];
  loading: boolean;
}) {
  const [dateRange, setDateRange] = useState<DateRangeKey>("30d");
  const [selectedFlow, setSelectedFlow] = useState<FlowType | null>(null);

  const filteredTransactions = filterTransactionsByRange(
    props.transactions,
    dateRange,
  );

  let incomeTotal = 0;
  let spendingTotal = 0;
  for (const transaction of filteredTransactions) {
    if (transaction.amount < 0) {
      incomeTotal += Math.abs(transaction.amount);
    } else {
      spendingTotal += transaction.amount;
    }
  }

  const netTotal = incomeTotal - spendingTotal;

  if (props.loading) {
    return (
      <section className="panel">
        <h2 className="panel-title">Charts</h2>
        <p>Loading chart data...</p>
      </section>
    );
  }

  if (!props.summary) {
    return (
      <section className="panel">
        <h2 className="panel-title">Charts</h2>
        <p>Login and sync data to view charts.</p>
      </section>
    );
  }

  const summaryBars = [
    { label: "Income", value: incomeTotal, flowType: "income" as const },
    {
      label: "Spending",
      value: spendingTotal,
      flowType: "spending" as const,
    },
    { label: "Net", value: Math.abs(netTotal), flowType: null },
  ];
  const maxSummary = Math.max(...summaryBars.map((entry) => entry.value), 1);

  const trendData = buildTrendData(
    filteredTransactions,
    getRangeDays(dateRange),
  );
  const maxTrend = Math.max(
    1,
    ...trendData.map((entry) => Math.max(entry.income, entry.spending)),
  );
  const breakdown = selectedFlow
    ? buildCategoryBreakdown(filteredTransactions, selectedFlow)
    : [];
  const maxBreakdown = Math.max(1, ...breakdown.map((entry) => entry.total));
  const categoryTransactions = filteredTransactions.filter((transaction) =>
    Boolean(transaction.personalFinanceCategoryPrimary),
  );
  const confidenceKnownCount = categoryTransactions.filter((transaction) =>
    Boolean(transaction.personalFinanceCategoryConfidenceLevel),
  ).length;
  const taxonomyVersions = Array.from(
    new Set(
      categoryTransactions
        .map(
          (transaction) => transaction.personalFinanceCategoryTaxonomyVersion,
        )
        .filter((version): version is string => Boolean(version)),
    ),
  );
  const taxonomyLabel =
    taxonomyVersions.length === 1
      ? taxonomyVersions[0]
      : taxonomyVersions.length > 1
        ? "mixed"
        : "unknown";

  return (
    <section className="panel">
      <h2 className="panel-title">Charts</h2>

      <div className="filter-row">
        {(["7d", "30d", "90d"] as DateRangeKey[]).map((range) => (
          <button
            key={range}
            className={`filter-chip ${dateRange === range ? "active" : ""}`}
            onClick={() => setDateRange(range)}
          >
            {range}
          </button>
        ))}
      </div>

      <div className="chart-block">
        <h3 className="chart-title">Range Overview</h3>
        {summaryBars.map((entry) => (
          <button
            key={entry.label}
            className={`bar-row clickable ${selectedFlow === entry.flowType ? "selected" : ""}`}
            onClick={() => {
              if (!entry.flowType) {
                return;
              }

              setSelectedFlow((current) =>
                current === entry.flowType ? null : entry.flowType,
              );
            }}
            disabled={!entry.flowType}
          >
            <span className="bar-label">{entry.label}</span>
            <div className="bar-track">
              <div
                className="bar-fill"
                style={{ width: `${(entry.value / maxSummary) * 100}%` }}
              />
            </div>
            <span className="bar-value">{entry.value.toFixed(2)}</span>
          </button>
        ))}
        <p className="hint-text">
          Click Income or Spending to view a category breakdown.
        </p>
        <p className="hint-text">
          PFC taxonomy: {taxonomyLabel}. Confidence on {confidenceKnownCount}/
          {categoryTransactions.length} categorized transactions.
        </p>
      </div>

      <div className="chart-block">
        <h3 className="chart-title">Recent Daily Trend</h3>
        {trendData.length === 0 ? (
          <p>No transaction data available for trend chart.</p>
        ) : (
          trendData.map((entry) => (
            <div key={entry.date} className="trend-row">
              <span className="trend-date">{entry.date.slice(5)}</span>
              <div className="trend-bars">
                <div className="trend-track">
                  <div
                    className="trend-fill income"
                    style={{ width: `${(entry.income / maxTrend) * 100}%` }}
                  />
                </div>
                <div className="trend-track">
                  <div
                    className="trend-fill spending"
                    style={{ width: `${(entry.spending / maxTrend) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {selectedFlow && (
        <div className="chart-block">
          <h3 className="chart-title">
            Top {selectedFlow === "spending" ? "Spending" : "Income"} Categories
            ({dateRange})
          </h3>
          {breakdown.length === 0 ? (
            <p>No categorized transactions found in this range.</p>
          ) : (
            <div className="breakdown-bars">
              {breakdown.map((entry) => (
                <div className="breakdown-row" key={entry.category}>
                  <div className="breakdown-header">
                    <span className="breakdown-category">{entry.category}</span>
                    <span className="breakdown-total">
                      {entry.total.toFixed(2)}
                    </span>
                  </div>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{
                        width: `${(entry.total / maxBreakdown) * 100}%`,
                      }}
                    />
                  </div>
                  <div className="breakdown-meta">
                    Top detail: {entry.topDetailedCategory} · {entry.count} txns
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export function App() {
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("password123");
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("pf_token"),
  );
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [transactions, setTransactions] = useState<
    TransactionListResponse["transactions"]
  >([]);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [authLoadingMode, setAuthLoadingMode] = useState<AuthMode | null>(null);
  const [isCreatingLinkToken, setIsCreatingLinkToken] = useState(false);
  const [isExchangingToken, setIsExchangingToken] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

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
          headers: {
            Authorization: `Bearer ${mfaToken}`,
          },
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
      setStatus("Passkey enabled and login completed");
      return;
    }

    setStatus("Verifying passkey (security key/biometrics)...");
    const options = await requestJson<any>(
      `${API_URL}/auth/webauthn/authenticate/options`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${mfaToken}`,
        },
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
    setStatus("Login completed with passkey");
  };

  const fetchDashboard = async (currentToken: string) => {
    const result = await requestJson<DashboardSummary>(
      `${API_URL}/finance/dashboard`,
      {
        headers: {
          Authorization: `Bearer ${currentToken}`,
        },
      },
      "loading dashboard",
    );
    setSummary(result);
  };

  const fetchTransactions = async (currentToken: string) => {
    const result = await requestJson<TransactionListResponse>(
      `${API_URL}/finance/transactions`,
      {
        headers: {
          Authorization: `Bearer ${currentToken}`,
        },
      },
      "loading transactions",
    );
    setTransactions(result.transactions);
  };

  const refreshData = async (currentToken: string) => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        fetchDashboard(currentToken),
        fetchTransactions(currentToken),
      ]);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    if (!token) {
      setSummary(null);
      setTransactions([]);
      setIsRefreshing(false);
      return;
    }

    const run = async () => {
      try {
        await refreshData(token);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      }
    };

    void run();
  }, [token]);

  const { open: openPlaid, ready: plaidReady } = usePlaidLink({
    token: linkToken,
    onSuccess: async (publicToken) => {
      if (!token) {
        return;
      }

      try {
        setIsExchangingToken(true);
        setStatus("Exchanging Plaid public token...");
        await requestJson<{ userId: string; linked: boolean }>(
          `${API_URL}/plaid/exchange-token`,
          {
            method: "POST",
            headers: withAuthHeader(token),
            body: JSON.stringify({ publicToken }),
          },
          "linking account",
        );

        setError(null);
        setStatus("Plaid account linked successfully");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setIsExchangingToken(false);
      }
    },
  });

  const auth = async (mode: AuthMode) => {
    setAuthLoadingMode(mode);
    setStatus("Working...");
    setError(null);

    try {
      const payload = await requestJson<AuthApiResponse>(
        `${API_URL}/auth/${mode}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email, password }),
        },
        mode === "login" ? "logging in" : "registering account",
      );

      if (payload.token) {
        localStorage.setItem("pf_token", payload.token);
        setToken(payload.token);
        setStatus(`${mode} successful`);
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
      setAuthLoadingMode(null);
    }
  };

  const logout = () => {
    localStorage.removeItem("pf_token");
    setToken(null);
    setStatus("Logged out");
    setLinkToken(null);
    setTransactions([]);
  };

  const createLinkToken = async () => {
    if (!token) {
      setError("Please login first");
      return;
    }

    try {
      setIsCreatingLinkToken(true);
      setStatus("Creating Plaid link token...");
      const payload = await requestJson<{ linkToken: string }>(
        `${API_URL}/plaid/create-link-token`,
        {
          method: "POST",
          headers: withAuthHeader(token),
        },
        "creating Plaid link token",
      );

      setLinkToken(payload.linkToken);
      setError(null);
      setStatus("Plaid link token ready. Click 'Open Plaid Link'.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsCreatingLinkToken(false);
    }
  };

  const runManualSync = async () => {
    if (!token) {
      setError("Please login first");
      return;
    }

    try {
      setIsSyncing(true);
      setStatus("Running manual sync...");
      const payload = await requestJson<ManualSyncResponse>(
        `${API_URL}/sync/manual`,
        {
          method: "POST",
          headers: withAuthHeader(token),
        },
        "running manual sync",
      );

      setError(null);
      setStatus(
        `Manual sync complete. Processed ${payload.syncedTransactions} changes.`,
      );
      await refreshData(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <main className="app-shell">
      <h1>Personal Finances (TS Rewrite)</h1>
      <p className="subtext">Finance-only MVP scaffold with NestJS + React.</p>

      <AuthSection
        email={email}
        password={password}
        disabled={false}
        authLoadingMode={authLoadingMode}
        onEmailChange={setEmail}
        onPasswordChange={setPassword}
        onRegister={() => void auth("register")}
        onLogin={() => void auth("login")}
        onLogout={logout}
      />

      {token && (
        <PlaidActions
          disabled={false}
          linkTokenReady={Boolean(linkToken)}
          plaidReady={plaidReady}
          creatingLinkToken={isCreatingLinkToken}
          exchangingToken={isExchangingToken}
          syncing={isSyncing}
          onCreateLinkToken={() => void createLinkToken()}
          onOpenPlaid={() => openPlaid()}
          onRunManualSync={() => void runManualSync()}
        />
      )}

      {status && <p className="status success">{status}</p>}
      {error && <p className="status error">Error: {error}</p>}

      <DashboardPanel summary={summary} loading={isRefreshing} />

      <ChartsPanel
        summary={summary}
        transactions={transactions}
        loading={isRefreshing}
      />

      {token && (
        <TransactionsPanel transactions={transactions} loading={isRefreshing} />
      )}
    </main>
  );
}
