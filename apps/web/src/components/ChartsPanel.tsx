import { TransactionRecord } from "@personal-finances/contracts";
import { Paper, Typography, Box, CircularProgress, Grid } from "@mui/material";
import { LineChart } from "@mui/x-charts/LineChart";
import { BarChart } from "@mui/x-charts/BarChart";

// Helper to group transactions by date for the trend line
function buildTrendData(transactions: TransactionRecord[]) {
  const grouped = new Map<
    string,
    { date: string; income: number; spending: number }
  >();
  for (let i = 29; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    grouped.set(d.toISOString().slice(0, 10), {
      date: d.toISOString().slice(5, 10),
      income: 0,
      spending: 0,
    });
  }

  for (const t of transactions) {
    if (grouped.has(t.date)) {
      const entry = grouped.get(t.date)!;
      if (t.amount < 0) entry.income += Math.abs(t.amount);
      else entry.spending += t.amount;
    }
  }
  return Array.from(grouped.values());
}

// Helper for top merchants/categories (Bar chart view)
function buildTopSpendingData(transactions: TransactionRecord[]) {
  const grouped = new Map<string, number>();
  for (const t of transactions) {
    if (t.amount < 0) continue; // Only spending
    const label = t.merchant || "Unknown";
    grouped.set(label, (grouped.get(label) ?? 0) + t.amount);
  }
  return Array.from(grouped.entries())
    .map(([label, amount]) => ({ label, amount }))
    .sort((a, b) => b.amount - a.amount)
    .slice(0, 5);
}

export function ChartsPanel({
  transactions,
  loading,
}: {
  transactions: TransactionRecord[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 5 }}>
        <CircularProgress />
      </Box>
    );
  }

  const trendData = buildTrendData(transactions);
  const spendingData = buildTopSpendingData(transactions);

  return (
    <Grid container spacing={3} sx={{ mb: 3 }}>
      {/* 50% width on desktop, 100% on mobile */}
      <Grid item xs={12} md={6}>
        <Paper elevation={2} sx={{ p: 3, borderRadius: 2, height: "100%" }}>
          <Typography variant="h6" gutterBottom>
            Cashflow Trend
          </Typography>
          <Box sx={{ width: "100%", height: 300 }}>
            <LineChart
              dataset={trendData}
              xAxis={[{ scaleType: "point", dataKey: "date" }]}
              series={[
                {
                  dataKey: "income",
                  label: "Income",
                  color: "#2e7d32",
                  curve: "monotoneX",
                  showMark: false,
                },
                {
                  dataKey: "spending",
                  label: "Spending",
                  color: "#d32f2f",
                  curve: "monotoneX",
                  showMark: false,
                },
              ]}
              margin={{ top: 20, bottom: 30, left: 50, right: 20 }}
            />
          </Box>
        </Paper>
      </Grid>

      {/* 50% width on desktop, 100% on mobile */}
      <Grid item xs={12} md={6}>
        <Paper elevation={2} sx={{ p: 3, borderRadius: 2, height: "100%" }}>
          <Typography variant="h6" gutterBottom>
            Top Merchants
          </Typography>
          <Box sx={{ width: "100%", height: 300 }}>
            <BarChart
              dataset={spendingData}
              yAxis={[{ scaleType: "band", dataKey: "label" }]}
              series={[{ dataKey: "amount", color: "#1976d2" }]}
              layout="horizontal"
              margin={{ left: 100, right: 20, top: 20, bottom: 30 }}
            />
          </Box>
        </Paper>
      </Grid>
    </Grid>
  );
}
