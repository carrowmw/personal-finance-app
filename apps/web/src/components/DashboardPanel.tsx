import { DashboardSummary } from "@personal-finances/contracts";
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Box,
  Skeleton,
} from "@mui/material";
import AccountBalanceWalletIcon from "@mui/icons-material/AccountBalanceWallet";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import SavingsIcon from "@mui/icons-material/Savings";

export function DashboardPanel(props: {
  summary: DashboardSummary | null;
  loading: boolean;
}) {
  if (props.loading || !props.summary) {
    return (
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {[1, 2, 3, 4].map((i) => (
          <Grid item xs={12} sm={6} md={3} key={i}>
            <Skeleton variant="rounded" height={118} />
          </Grid>
        ))}
      </Grid>
    );
  }

  // Calculate a 4th metric: Savings Rate
  const savingsRate =
    props.summary.incomeMonth > 0
      ? (props.summary.netCashflowMonth / props.summary.incomeMonth) * 100
      : 0;

  const cards = [
    {
      title: "Net Cashflow",
      value: `$${Math.abs(props.summary.netCashflowMonth).toLocaleString("en-US", { minimumFractionDigits: 2 })}`,
      icon: <AccountBalanceWalletIcon color="primary" sx={{ fontSize: 40 }} />,
      color: "text.primary",
    },
    {
      title: "Income",
      value: `$${props.summary.incomeMonth.toLocaleString("en-US", { minimumFractionDigits: 2 })}`,
      icon: <TrendingUpIcon color="success" sx={{ fontSize: 40 }} />,
      color: "success.main",
    },
    {
      title: "Spending",
      value: `$${props.summary.spendingMonth.toLocaleString("en-US", { minimumFractionDigits: 2 })}`,
      icon: <TrendingDownIcon color="error" sx={{ fontSize: 40 }} />,
      color: "error.main",
    },
    {
      title: "Savings Rate",
      value: `${savingsRate.toFixed(1)}%`,
      icon: <SavingsIcon color="info" sx={{ fontSize: 40 }} />,
      color: "info.main",
    },
  ];

  return (
    <Grid container spacing={3} sx={{ mb: 3 }}>
      {cards.map((card) => (
        // Breakpoints: Mobile=1 column (12), Tablet=2 cols (6), Desktop=4 cols (3)
        <Grid item xs={12} sm={6} md={3} key={card.title}>
          <Card elevation={2} sx={{ borderRadius: 2, height: "100%" }}>
            <CardContent>
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                }}
              >
                <Box>
                  <Typography
                    color="text.secondary"
                    variant="subtitle2"
                    gutterBottom
                  >
                    {card.title} (30d)
                  </Typography>
                  <Typography
                    variant="h5"
                    component="div"
                    sx={{ color: card.color, fontWeight: "bold" }}
                  >
                    {card.value}
                  </Typography>
                </Box>
                {card.icon}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
}
