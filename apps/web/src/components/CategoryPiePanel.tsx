import { TransactionRecord } from "@personal-finances/contracts";
import { Paper, Typography, Box, CircularProgress } from "@mui/material";
import { PieChart } from "@mui/x-charts/PieChart";

export function CategoryPiePanel({
  transactions,
  loading,
}: {
  transactions: TransactionRecord[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <Paper
        elevation={2}
        sx={{
          p: 3,
          borderRadius: 2,
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <CircularProgress />
      </Paper>
    );
  }

  // Aggregate spending by category
  const grouped = new Map<string, number>();
  for (const t of transactions) {
    if (t.amount < 0) continue; // Only count spending
    const cat = t.personalFinanceCategoryPrimary ?? "Other";
    grouped.set(cat, (grouped.get(cat) ?? 0) + t.amount);
  }

  // MUI PieChart expects an array of objects with id, value, and label
  const data = Array.from(grouped.entries())
    .map(([label, value], index) => ({ id: index, value, label }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 6); // Keep it to top 6 so the legend doesn't overflow

  return (
    <Paper elevation={2} sx={{ p: 3, borderRadius: 2, height: "100%" }}>
      <Typography variant="h6" gutterBottom>
        Spending by Category
      </Typography>
      <Box
        sx={{
          width: "100%",
          height: 350,
          display: "flex",
          alignItems: "center",
        }}
      >
        {data.length > 0 ? (
          <PieChart
            series={[
              {
                data,
                innerRadius: 30,
                paddingAngle: 2,
                cornerRadius: 4,
              },
            ]}
            // Hiding the legend to save space in a 1/4 width card,
            // the tooltip handles identifying the slices perfectly.
            slotProps={{ legend: { hidden: true } }}
            margin={{ top: 10, bottom: 10, left: 10, right: 10 }}
          />
        ) : (
          <Typography color="text.secondary" sx={{ mx: "auto" }}>
            No data
          </Typography>
        )}
      </Box>
    </Paper>
  );
}
