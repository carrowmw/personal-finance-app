# application/frontend/dash_app/layout.py

from dash import html, dcc, dash_table, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

from application.data.processing import get_transactions_df, get_monthly_spending


def create_spending_overview(username):
    """Create an overview of spending trends"""
    df = get_transactions_df(username)
    if df is None:
        return None

    # Convert date to datetime if it's not already
    df["date"] = pd.to_datetime(df["date"])

    # Create monthly spending trend
    monthly_spending = df.groupby(df["date"].dt.strftime("%Y-%m"))["amount"].sum()

    fig = go.Figure()

    # Add bar chart for monthly spending
    fig.add_trace(
        go.Bar(
            x=monthly_spending.index, y=monthly_spending.values, name="Monthly Spending"
        )
    )

    # Add trend line
    fig.add_trace(
        go.Scatter(
            x=monthly_spending.index,
            y=monthly_spending.values.rolling(3).mean(),
            name="3-Month Average",
            line=dict(color="red"),
        )
    )

    fig.update_layout(
        title="Monthly Spending Overview",
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        hovermode="x unified",
    )

    return fig


def create_category_sunburst(username):
    """Create a sunburst chart of spending by category and subcategory"""
    df = get_transactions_df(username)
    if df is None:
        return None

    # Group by category and subcategory
    grouped = df.groupby(["category", "subcategory"])["amount"].sum().reset_index()

    fig = px.sunburst(
        grouped,
        path=["category", "subcategory"],
        values="amount",
        title="Spending Distribution",
    )

    fig.update_layout(width=600, height=600)

    return fig


def create_transactions_by_category_graph(username):
    """Create a bar chart of spending by category"""
    df = get_transactions_df(username)
    if df is None:
        return None

    # Group by category
    category_spending = (
        df.groupby("category")["amount"].sum().sort_values(ascending=True)
    )

    fig = go.Figure(
        go.Bar(x=category_spending.values, y=category_spending.index, orientation="h")
    )

    fig.update_layout(
        title="Spending by Category",
        xaxis_title="Amount ($)",
        yaxis_title="Category",
        height=400
        + (len(category_spending) * 20),  # Adjust height based on number of categories
    )

    return fig


def create_recent_transactions_table(username):
    """Create a table of recent transactions"""
    df = get_transactions_df(username)
    if df is None:
        return None

    # Sort by date and get recent transactions
    recent_df = df.sort_values("date", ascending=False).head(10)

    # Format amounts as currency
    recent_df["amount"] = recent_df["amount"].apply(lambda x: f"${x:,.2f}")

    return dash_table.DataTable(
        id="recent-transactions",
        columns=[
            {"name": "Date", "id": "date"},
            {"name": "Name", "id": "name"},
            {"name": "Amount", "id": "amount"},
            {"name": "Category", "id": "category"},
            {"name": "Subcategory", "id": "subcategory"},
        ],
        data=recent_df.to_dict("records"),
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left", "padding": "10px", "minWidth": "100px"},
        style_header={"backgroundColor": "rgb(230, 230, 230)", "fontWeight": "bold"},
    )


def create_layout(username):
    """Create the main dashboard layout"""
    return html.Div(
        [
            dbc.Container(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H1(
                                        "Financial Dashboard",
                                        className="text-center mb-4",
                                    ),
                                ],
                                width=12,
                            )
                        ]
                    ),
                    # Spending Overview
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardBody(
                                                [
                                                    html.H3("Spending Overview"),
                                                    dcc.Graph(
                                                        id="spending-overview",
                                                        figure=create_spending_overview(
                                                            username
                                                        ),
                                                    ),
                                                ]
                                            )
                                        ]
                                    )
                                ],
                                width=12,
                            )
                        ],
                        className="mb-4",
                    ),
                    # Category Analysis
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardBody(
                                                [
                                                    html.H3("Category Distribution"),
                                                    dcc.Graph(
                                                        id="category-sunburst",
                                                        figure=create_category_sunburst(
                                                            username
                                                        ),
                                                    ),
                                                ]
                                            )
                                        ]
                                    )
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardBody(
                                                [
                                                    html.H3("Spending by Category"),
                                                    dcc.Graph(
                                                        id="category-bar",
                                                        figure=create_transactions_by_category_graph(
                                                            username
                                                        ),
                                                    ),
                                                ]
                                            )
                                        ]
                                    )
                                ],
                                width=6,
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Recent Transactions
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardBody(
                                                [
                                                    html.H3("Recent Transactions"),
                                                    create_recent_transactions_table(
                                                        username
                                                    ),
                                                ]
                                            )
                                        ]
                                    )
                                ],
                                width=12,
                            )
                        ]
                    ),
                ],
                fluid=True,
            )
        ]
    )


# Callbacks
@callback(
    Output("category-sunburst", "figure"), Input("spending-overview", "clickData")
)
def update_category_view(click_data):
    if click_data is None:
        return create_category_sunburst()
    # Add logic here to filter by clicked month if desired
    return create_category_sunburst()
