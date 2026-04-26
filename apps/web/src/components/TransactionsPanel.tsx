import { TransactionRecord } from "@personal-finances/contracts";

export function TransactionsPanel(props: {
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
