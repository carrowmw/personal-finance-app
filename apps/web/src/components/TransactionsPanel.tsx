import { TransactionRecord } from "@personal-finances/contracts";
import {
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from "@mui/material";

export function TransactionsPanel({
  transactions,
  loading,
}: {
  transactions: TransactionRecord[];
  loading: boolean;
}) {
  return (
    <Paper
      elevation={2}
      sx={{ p: 0, borderRadius: 2, overflow: "hidden", mt: 3 }}
    >
      <Typography variant="h6" sx={{ p: 3, pb: 2 }}>
        Recent Transactions
      </Typography>
      <TableContainer sx={{ maxHeight: 500 }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Merchant</TableCell>
              <TableCell>Category</TableCell>
              <TableCell align="right">Amount</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : transactions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  No transactions found.
                </TableCell>
              </TableRow>
            ) : (
              transactions.map((t) => (
                <TableRow key={t.id} hover>
                  <TableCell sx={{ whiteSpace: "nowrap" }}>{t.date}</TableCell>
                  <TableCell>{t.merchant}</TableCell>
                  <TableCell>
                    <Chip
                      label={
                        t.personalFinanceCategoryPrimary ?? "Uncategorized"
                      }
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{
                      fontWeight: "bold",
                      color: t.amount < 0 ? "success.main" : "inherit",
                    }}
                  >
                    {t.amount < 0 ? "+" : ""}${Math.abs(t.amount).toFixed(2)}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}
