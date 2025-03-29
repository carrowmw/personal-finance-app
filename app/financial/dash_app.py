# app/financial/dash_app.py

"""
Handles the analytics page visualizations.
"""

import pandas as pd
import dash
from dash import html, dcc, callback, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from flask_login import current_user
from app.financial.services import get_transactions_df, get_spending_by_category
import json
from plotly.utils import PlotlyJSONEncoder


# Modify these functions in app/financial/dash_app.py


def generate_spending_chart(
    username, start_date=None, end_date=None, categories=None, accounts=None
):
    """Generate the spending overview chart data."""
    # Get transactions dataframe
    df = get_transactions_df(username)
    if df is None or len(df) == 0:
        print("No transactions data for spending chart")
        # Return empty figure
        fig = go.Figure()
        fig.add_annotation(
            text="No transaction data available", x=0.5, y=0.5, showarrow=False
        )
        return json.dumps(fig, cls=PlotlyJSONEncoder)

    print(f"Generating spending chart with {len(df)} transactions")

    # Create a copy of the dataframe to avoid the warning
    df = df.copy()

    # Apply filters
    df.loc[:, "date"] = pd.to_datetime(df["date"])

    if start_date:
        df = df[df["date"] >= pd.to_datetime(start_date)]
        print(f"After start_date filter: {len(df)} transactions")

    if end_date:
        df = df[df["date"] <= pd.to_datetime(end_date)]
        print(f"After end_date filter: {len(df)} transactions")

    if categories and "category" in df.columns:
        category_list = categories.split(",")
        df = df[df["category"].isin(category_list)]
        print(f"After category filter: {len(df)} transactions")

    if accounts and "account_id" in df.columns:
        account_list = accounts.split(",")
        df = df[df["account_id"].isin(account_list)]
        print(f"After account filter: {len(df)} transactions")

    if len(df) == 0:
        print("No transactions after filtering")
        fig = go.Figure()
        fig.add_annotation(
            text="No transaction data available for the selected filters",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return json.dumps(fig, cls=PlotlyJSONEncoder)

    # Create monthly trend chart - Group by year-month
    df.loc[:, "month"] = df["date"].dt.strftime("%Y-%m")
    monthly_df = df.groupby("month")["amount"].sum().reset_index()
    monthly_df = monthly_df.sort_values("month")

    print(f"Monthly data: {monthly_df.to_dict('records')}")

    # Create figure
    fig = go.Figure(
        data=[
            go.Bar(
                x=monthly_df["month"], y=monthly_df["amount"], marker_color="#4e73df"
            )
        ]
    )

    fig.update_layout(
        title="Monthly Spending Trend",
        xaxis_title="Month",
        yaxis_title="Amount (£)",
        yaxis=dict(tickprefix="£"),
        height=400,
        margin=dict(l=20, r=20, t=40, b=40),
    )

    return json.dumps(fig, cls=PlotlyJSONEncoder)


def generate_category_chart(
    username, start_date=None, end_date=None, categories=None, accounts=None
):
    """Generate the category breakdown chart data."""
    # Get transactions dataframe first for filtering
    df = get_transactions_df(username)
    if df is None or len(df) == 0:
        print("No transactions data for category chart")
        # Return empty figure
        fig = go.Figure()
        fig.add_annotation(
            text="No transaction data available", x=0.5, y=0.5, showarrow=False
        )
        return json.dumps(fig, cls=PlotlyJSONEncoder)

    print(f"Generating category chart with {len(df)} transactions")

    # Create a copy of the dataframe to avoid the warning
    df = df.copy()

    # Apply filters
    df.loc[:, "date"] = pd.to_datetime(df["date"])

    if start_date:
        df = df[df["date"] >= pd.to_datetime(start_date)]
        print(f"After start_date filter: {len(df)} transactions")

    if end_date:
        df = df[df["date"] <= pd.to_datetime(end_date)]
        print(f"After end_date filter: {len(df)} transactions")

    if accounts and "account_id" in df.columns:
        account_list = accounts.split(",")
        df = df[df["account_id"].isin(account_list)]
        print(f"After account filter: {len(df)} transactions")

    # Filter for expenses only (positive amounts)
    if "amount" in df.columns:
        expenses_df = df[df["amount"] > 0].copy()
        print(f"Expense transactions: {len(expenses_df)}")
    else:
        expenses_df = pd.DataFrame()
        print("No amount column in transactions")

    if len(expenses_df) == 0:
        print("No expense transactions found")
        fig = go.Figure()
        fig.add_annotation(
            text="No expense data available", x=0.5, y=0.5, showarrow=False
        )
        return json.dumps(fig, cls=PlotlyJSONEncoder)

    # Group by category and sum amounts
    if "category" in expenses_df.columns:
        expenses_df.loc[:, "category"] = expenses_df["category"].fillna("Uncategorized")
        categories_data = expenses_df.groupby("category")["amount"].sum()

        print(f"Categories found: {categories_data.index.tolist()}")
        print(f"Category amounts: {categories_data.values.tolist()}")

        if len(categories_data) == 0:
            print("No categories after grouping")
            fig = go.Figure()
            fig.add_annotation(
                text="No categorized data available", x=0.5, y=0.5, showarrow=False
            )
            return json.dumps(fig, cls=PlotlyJSONEncoder)

        top_categories = categories_data.nlargest(5)
        print(f"Top 5 categories: {top_categories.index.tolist()}")

        # Add "Other" category for the rest
        if len(categories_data) > 5:
            other_sum = categories_data.nsmallest(len(categories_data) - 5).sum()
            if other_sum > 0:  # Only add if there's actually an "Other" amount
                top_categories["Other"] = other_sum

        # Create pie chart
        colors = ["#4e73df", "#1cc88a", "#36b9cc", "#f6c23e", "#e74a3b", "#aaaaaa"]

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=top_categories.index,
                    values=top_categories.values,
                    hole=0.7,
                    marker=dict(colors=colors[: len(top_categories)]),
                )
            ]
        )

        fig.update_layout(
            title="Spending by Category",
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.1, x=0.5, xanchor="center"
            ),
            margin=dict(l=20, r=20, t=40, b=20),
            height=400,
        )

        return json.dumps(fig, cls=PlotlyJSONEncoder)
    else:
        # If no category column, return a simple chart
        print("No category column in expenses")
        total_spending = expenses_df["amount"].sum() if len(expenses_df) > 0 else 0
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=["Uncategorized"],
                    values=[total_spending],
                    hole=0.7,
                    marker=dict(colors=["#4e73df"]),
                )
            ]
        )
        fig.update_layout(
            title="Spending by Category",
            legend=dict(orientation="h"),
            margin=dict(l=20, r=20, t=40, b=20),
            height=400,
        )
        return json.dumps(fig, cls=PlotlyJSONEncoder)


def get_transactions_data(
    username, start_date=None, end_date=None, categories=None, accounts=None
):
    """Get transactions data for the table with filtering."""
    df = get_transactions_df(username)
    if df is None or len(df) == 0:
        print("No transactions found for transaction table data")
        return []

    print(
        f"Filtering transaction table data with: start={start_date}, end={end_date}, categories={categories}, accounts={accounts}"
    )

    # Apply filters
    df["date"] = pd.to_datetime(df["date"])

    if start_date:
        start_date = pd.to_datetime(start_date)
        df = df[df["date"] >= start_date]
        print(f"After start_date filter: {len(df)} transactions")

    if end_date:
        end_date = pd.to_datetime(end_date)
        df = df[df["date"] <= end_date]
        print(f"After end_date filter: {len(df)} transactions")

    if categories and "category" in df.columns:
        category_list = [cat.strip() for cat in categories.split(",") if cat.strip()]
        if category_list:
            df = df[df["category"].isin(category_list)]
            print(f"After category filter: {len(df)} transactions")

    if accounts and "account_id" in df.columns:
        account_list = [acc.strip() for acc in accounts.split(",") if acc.strip()]
        if account_list:
            df = df[df["account_id"].isin(account_list)]
            print(f"After account filter: {len(df)} transactions")

    # Format date column
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # Sort by date, descending
    df = df.sort_values("date", ascending=False)

    # Return as records
    return df.to_dict("records")


def get_category_options(username):
    """Get unique categories from user transactions for dropdown."""
    df = get_transactions_df(username)
    if df is None or len(df) == 0 or "category" not in df.columns:
        return []

    # Get unique categories and clean them up
    categories = df["category"].dropna().unique()

    # Convert categories to a list, filtering out None values
    categories = [cat for cat in categories if cat is not None]

    # Sort alphabetically
    categories.sort()

    # Return as list of objects with value and label
    return [{"value": cat, "label": cat} for cat in categories]
