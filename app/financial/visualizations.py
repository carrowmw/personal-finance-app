# app/financial/visualizations.py

"""
Creates the charts for the dashboards.
"""

import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import pandas as pd


import plotly.graph_objects as go
import plotly.io as pio


def create_category_chart_html(category_data):
    """Create complete HTML for category pie chart using Plotly"""
    if (
        not category_data
        or not isinstance(category_data, dict)
        or "labels" not in category_data
        or "values" not in category_data
        or not category_data["labels"]
        or len(category_data["labels"]) == 0
    ):
        # Return a message for empty data
        fig = go.Figure()
        fig.add_annotation(
            text="No category data available for the selected filters",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14),
        )
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")

    try:
        # Ensure values are serializable (convert any complex types to float)
        labels = category_data["labels"]
        values = [float(val) for val in category_data["values"]]

        # Create pie chart with Plotly
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.7,
                    textinfo="label+percent",
                    marker=dict(
                        colors=[
                            "#4e73df",
                            "#1cc88a",
                            "#36b9cc",
                            "#f6c23e",
                            "#e74a3b",
                            "#aaaaaa",
                        ]
                    ),
                )
            ]
        )

        fig.update_layout(
            title="Spending by Category",
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            margin=dict(l=20, r=20, t=40, b=0),
            height=600,
        )

        # Add a note about the filters if they were applied
        fig.add_annotation(
            text="Note: Filtered data shown",
            x=0.5,
            y=1.05,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=10, color="gray"),
        )

        # Convert the figure to HTML
        return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
    except Exception as e:
        print(f"Error creating category chart: {str(e)}")
        return f"<div class='text-center py-5'><p class='text-danger'>Error creating chart: {str(e)}</p></div>"


def create_spending_chart_html(monthly_data):
    """Create complete HTML for monthly spending bar chart using Plotly"""
    if (
        not monthly_data
        or not isinstance(monthly_data, dict)
        or "labels" not in monthly_data
        or "values" not in monthly_data
        or not monthly_data["labels"]
        or len(monthly_data["labels"]) == 0
    ):
        # Return a message for empty data
        fig = go.Figure()
        fig.add_annotation(
            text="No spending data available for the selected filters",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14),
        )
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=40, b=40),
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")

    try:
        # Ensure values are serializable
        labels = monthly_data["labels"]
        values = [float(val) for val in monthly_data["values"]]

        # Create a bar chart with Plotly
        fig = go.Figure(
            data=[
                go.Bar(
                    x=labels,
                    y=values,
                    marker_color="#4e73df",
                    hovertemplate="%{y:,.2f} £<extra>%{x}</extra>",
                )
            ]
        )

        fig.update_layout(
            title="Monthly Spending Trend",
            xaxis_title="Month",
            yaxis_title="Amount (£)",
            yaxis=dict(tickprefix="£"),
            height=300,
            margin=dict(l=20, r=20, t=40, b=40),
        )

        # Add a note about the filters if they were applied
        fig.add_annotation(
            text="Note: Filtered data shown",
            x=0.5,
            y=1.05,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=10, color="gray"),
        )

        # Convert the figure to HTML
        return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
    except Exception as e:
        print(f"Error creating spending chart: {str(e)}")
        return f"<div class='text-center py-5'><p class='text-danger'>Error creating chart: {str(e)}</p></div>"


def create_monthly_trend_json(monthly_data):
    """Create JSON data for an API endpoint for a monthly trend chart"""
    if not monthly_data or not monthly_data.get("labels"):
        return json.dumps({"error": "No data available"})

    try:
        # Convert values to float to ensure they're serializable
        values = [
            (
                float(val)
                if hasattr(val, "__float__")
                else float(val) if isinstance(val, (int, str)) and val else 0
            )
            for val in monthly_data.get("values", [])
        ]
        counts = [
            (
                int(count)
                if hasattr(count, "__int__")
                else int(count) if isinstance(count, (int, str)) and count else 0
            )
            for count in monthly_data.get("counts", [])
        ]

        result = {
            "labels": monthly_data["labels"],
            "datasets": [
                {
                    "label": "Monthly Spending",
                    "data": values,
                    "backgroundColor": "#4e73df",
                    "borderColor": "#4e73df",
                    "borderWidth": 1,
                },
            ],
        }

        # Only add counts if they exist
        if "counts" in monthly_data and all(
            isinstance(c, (int, float)) for c in counts
        ):
            result["datasets"].append(
                {
                    "label": "Transaction Count",
                    "data": counts,
                    "backgroundColor": "#1cc88a",
                    "borderColor": "#1cc88a",
                    "borderWidth": 1,
                    "yAxisID": "count",
                }
            )

        return json.dumps(result)
    except Exception as e:
        print(f"Error serializing monthly trend data: {str(e)}")
        return json.dumps({"error": "Error creating chart data"})


def create_portfolio_chart(balances):
    """Create a portfolio allocation chart."""
    if not balances:
        return json.dumps({"error": "No balance data available"})

    try:
        # Group accounts by type
        account_types = {}
        for balance in balances:
            account_type = balance.type.capitalize()
            if account_type not in account_types:
                account_types[account_type] = 0

            # Add balance value (ensure it's positive for visualization)
            account_types[account_type] += abs(float(balance.current_balance))

        # Create data
        labels = list(account_types.keys())
        values = [float(val) for val in account_types.values()]

        # Create doughnut chart config
        chart_config = {
            "type": "doughnut",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "data": values,
                        "backgroundColor": [
                            "#4e73df",
                            "#1cc88a",
                            "#36b9cc",
                            "#f6c23e",
                            "#e74a3b",
                            "#aaaaaa",
                        ][: len(labels)],
                        "hoverOffset": 4,
                    }
                ],
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "plugins": {
                    "legend": {"position": "bottom"},
                    "tooltip": {
                        "callbacks": {
                            "label": "function(context) { return context.label + ': £' + context.raw.toFixed(2); }"
                        }
                    },
                },
                "cutout": "70%",
            },
        }

        return json.dumps(chart_config)
    except Exception as e:
        print(f"Error creating portfolio chart: {str(e)}")
        return json.dumps({"error": "Error creating chart"})
