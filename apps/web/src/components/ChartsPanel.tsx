import { useState } from "react";
import {
  DashboardSummary,
  TransactionRecord,
} from "@personal-finances/contracts";

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

export function ChartsPanel(props: {
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
