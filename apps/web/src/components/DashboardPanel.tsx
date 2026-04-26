import { DashboardSummary } from "@personal-finances/contracts";

export function DashboardPanel(props: {
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
