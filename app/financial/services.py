# app/financial/services.py

"""
Provides the underlying data for the dashboards.
"""

import pandas as pd
from app.models import Transaction, Balance, User
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func
from decimal import Decimal


def get_transactions(
    user_id, start_date=None, end_date=None, account_id=None, limit=None
):
    """Get transactions for a user within a date range."""
    query = Transaction.query.filter_by(user_id=user_id)

    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)

    # Order by date, most recent first
    query = query.order_by(Transaction.date.desc())

    if limit:
        query = query.limit(limit)

    return query.all()


def get_balances(user_id):
    """Get all account balances for a user."""
    return Balance.query.filter_by(user_id=user_id).all()


def get_transactions_df(username):
    """Get transactions for a user and convert to a pandas DataFrame."""
    user = User.query.filter_by(username=username).first()
    if not user:
        return None

    transactions = Transaction.query.filter_by(user_id=user.id).all()
    if not transactions:
        return pd.DataFrame()  # Return empty DataFrame instead of None

    # Convert to list of dictionaries for pandas
    transactions_data = [
        {
            "account_id": t.account_id,
            "amount": float(t.amount),
            "category": t.category,
            "date": t.date,
            "merchant_name": t.merchant_name,
            "name": t.name,
            "pending": t.pending,
            "account_name": t.account_name,  # Include account_name if available
        }
        for t in transactions
    ]

    # Create DataFrame
    df = pd.DataFrame(transactions_data)

    # Print DataFrame info for debugging
    print(f"Transactions DataFrame: {len(df)} rows")
    if len(df) > 0:
        print(f"Columns: {df.columns.tolist()}")
        print(f"Sample data: {df.head(2).to_dict('records')}")

    # If DataFrame is empty, return it
    if len(df) == 0:
        return df

    # Process category data if needed
    if "category" in df.columns:
        # Handle NaN values
        df.loc[:, "category"] = df["category"].fillna("Uncategorized")

        # Split into main categories if it contains '/'
        df.loc[:, "category"] = df["category"].apply(
            lambda x: x.split("/")[-1] if x and "/" in x else x
        )

    return df


def get_transaction_summary(username):
    """Get summary statistics for a user's transactions."""
    df = get_transactions_df(username)
    if df is None or len(df) == 0:
        return {
            "total_transactions": 0,
            "total_spent": 0,
            "average_transaction": 0,
            "top_categories": {},
        }

    # Calculate summary statistics
    summary = {
        "total_transactions": len(df),
        "total_spent": round(df["amount"].sum(), 2),
        "average_transaction": round(df["amount"].mean(), 2),
        "top_categories": (
            df.groupby("category")["amount"].sum().nlargest(5).to_dict()
            if "category" in df.columns
            else {}
        ),
    }

    return summary


def calculate_monthly_spending(username, with_details=False):
    """Get monthly spending totals for a user."""
    df = get_transactions_df(username)
    if df is None or len(df) == 0:
        print("No transactions found for monthly spending calculation")
        return 0 if not with_details else {"labels": [], "values": [], "counts": []}

    print(f"Calculate monthly spending with {len(df)} transactions")

    # Convert date to datetime if it's not already
    df.loc[:, "date"] = pd.to_datetime(df["date"])

    # Filter to current month for simple total
    current_month = datetime.now().replace(day=1).date()
    current_month_df = df[df["date"] >= pd.Timestamp(current_month)]
    print(f"Current month transactions: {len(current_month_df)}")

    # Only consider positive amounts as spending (debits)
    current_month_df_spend = current_month_df[current_month_df["amount"] > 0].copy()
    print(f"Current month spending transactions: {len(current_month_df_spend)}")

    current_month_spending = (
        current_month_df_spend["amount"].sum() if len(current_month_df_spend) > 0 else 0
    )
    print(f"Current month spending total: {current_month_spending}")

    if not with_details:
        return abs(float(current_month_spending))

    # For details, get last 6 months
    six_months_ago = (datetime.now() - timedelta(days=180)).replace(day=1).date()
    filtered_df = df[df["date"] >= pd.Timestamp(six_months_ago)].copy()
    print(f"Last 6 months transactions: {len(filtered_df)}")

    # Only consider positive amounts as spending (debits)
    filtered_df_spend = filtered_df[filtered_df["amount"] > 0].copy()
    print(f"Last 6 months spending transactions: {len(filtered_df_spend)}")

    # Group by month
    filtered_df_spend.loc[:, "month"] = filtered_df_spend["date"].dt.strftime("%Y-%m")
    monthly = (
        filtered_df_spend.groupby("month")
        .agg({"amount": "sum", "date": "count"})
        .rename(columns={"date": "transaction_count"})
    )

    print(f"Monthly grouping results: {len(monthly)} months")
    if len(monthly) > 0:
        print(f"Monthly data: {monthly.to_dict()}")

    # Sort by month
    monthly = monthly.sort_index()

    # Format month names more nicely
    month_labels = []
    month_values = []
    month_counts = []

    # Ensure we have data for all months in the last 6 months
    now = datetime.now()
    for i in range(5, -1, -1):  # Last 6 months
        month_date = (now - timedelta(days=30 * i)).replace(day=1)
        month_key = month_date.strftime("%Y-%m")
        month_label = month_date.strftime("%b %Y")

        if month_key in monthly.index:
            month_values.append(float(monthly.loc[month_key, "amount"]))
            month_counts.append(int(monthly.loc[month_key, "transaction_count"]))
        else:
            month_values.append(0)
            month_counts.append(0)

        month_labels.append(month_label)

    # Convert to a format suitable for charts
    result = {
        "labels": month_labels,
        "values": month_values,
        "counts": month_counts,
    }

    print(f"Monthly result: {result}")

    return result


def get_spending_by_category(username):
    """Get spending breakdown by category."""
    df = get_transactions_df(username)
    if df is None or len(df) == 0:
        print("No transactions found for category breakdown")
        return {"labels": [], "values": []}

    print(f"Get spending by category with {len(df)} transactions")

    # Filter for expenses only (positive amounts)
    if "amount" in df.columns:
        expenses_df = df[df["amount"] > 0].copy()
        print(f"Expense transactions: {len(expenses_df)}")
    else:
        expenses_df = pd.DataFrame()
        print("No amount column found in transactions")

    if len(expenses_df) == 0:
        print("No expense transactions found")
        return {"labels": [], "values": []}

    # Group by category and sum amounts
    if "category" in expenses_df.columns:
        # Ensure we have no NaN values in category
        expenses_df.loc[:, "category"] = expenses_df["category"].fillna("Uncategorized")

        categories = expenses_df.groupby("category")["amount"].sum()
        print(f"Categories found: {categories.index.tolist()}")
        print(f"Category amounts: {categories.values.tolist()}")

        if len(categories) == 0:
            print("No categories found after grouping")
            return {"labels": ["No Data"], "values": [0]}

        top_categories = categories.nlargest(5)
        print(f"Top 5 categories: {top_categories.index.tolist()}")

        # Add "Other" category for the rest
        if len(categories) > 5:
            other_sum = categories.nsmallest(len(categories) - 5).sum()
            if other_sum > 0:  # Only add if there's actually an "Other" amount
                top_categories["Other"] = other_sum

        result = {
            "labels": top_categories.index.tolist(),
            "values": top_categories.values.tolist(),
        }
        print(f"Category result: {result}")
        return result

    # If no category column, return all as "Uncategorized"
    if len(expenses_df) > 0:
        total_spending = expenses_df["amount"].sum()
        print(f"Uncategorized total spending: {total_spending}")
        return {"labels": ["Uncategorized"], "values": [float(total_spending)]}

    print("No data for category breakdown")
    return {"labels": [], "values": []}


def get_income_sources(username):
    """Get income sources breakdown."""
    df = get_transactions_df(username)
    if df is None or len(df) == 0:
        return {"labels": [], "values": []}

    # Filter for income only (negative amounts)
    income_df = df[df["amount"] < 0] if "amount" in df.columns else pd.DataFrame()

    if len(income_df) == 0:
        return {"labels": [], "values": []}

    # Use merchant_name as the source if available, otherwise use transaction name
    if "merchant_name" in income_df.columns:
        income_df["source"] = income_df["merchant_name"].fillna(income_df["name"])
    else:
        income_df["source"] = income_df["name"]

    # Group by source and sum amounts
    sources = income_df.groupby("source")["amount"].sum().abs()  # Convert to positive

    if len(sources) == 0:
        return {"labels": ["No Data"], "values": [0]}

    top_sources = sources.nlargest(5)

    # Add "Other" for the rest
    if len(sources) > 5:
        other_sum = sources.nsmallest(len(sources) - 5).sum()
        if other_sum > 0:
            top_sources["Other"] = other_sum

    return {
        "labels": top_sources.index.tolist(),
        "values": top_sources.values.tolist(),
    }


def get_monthly_data_with_filters(
    username, start_date=None, end_date=None, categories=None, accounts=None
):
    """Get monthly spending data with filters."""
    df = get_transactions_df(username)
    if df is None or len(df) == 0:
        print("No transactions found for monthly data with filters")
        return {"labels": [], "values": []}

    print(
        f"Filtering monthly data with: start={start_date}, end={end_date}, categories={categories}, accounts={accounts}"
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

    # Only consider positive amounts as spending (debits)
    df_spend = df[df["amount"] > 0].copy()
    print(f"Spending transactions: {len(df_spend)}")

    if len(df_spend) == 0:
        return {"labels": [], "values": []}

    # Group by month
    df_spend["month"] = df_spend["date"].dt.strftime("%Y-%m")
    monthly = df_spend.groupby("month")["amount"].sum().sort_index()

    # Format month names more nicely
    month_labels = []
    month_values = []

    for month, value in monthly.items():
        date = datetime.strptime(month, "%Y-%m")
        month_labels.append(date.strftime("%b %Y"))
        month_values.append(float(value))

    return {"labels": month_labels, "values": month_values}


def get_category_data_with_filters(
    username, start_date=None, end_date=None, categories=None, accounts=None
):
    """Get category spending data with filters."""
    df = get_transactions_df(username)
    if df is None or len(df) == 0:
        print("No transactions found for category data with filters")
        return {"labels": [], "values": []}

    print(
        f"Filtering category data with: start={start_date}, end={end_date}, categories={categories}, accounts={accounts}"
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

    if accounts and "account_id" in df.columns:
        account_list = [acc.strip() for acc in accounts.split(",") if acc.strip()]
        if account_list:
            df = df[df["account_id"].isin(account_list)]
            print(f"After account filter: {len(df)} transactions")

    # Filter for expenses only (positive amounts)
    expenses_df = df[df["amount"] > 0].copy()
    print(f"Expense transactions: {len(expenses_df)}")

    if len(expenses_df) == 0:
        return {"labels": [], "values": []}

    # Apply category filter after getting expenses
    if categories and "category" in expenses_df.columns:
        category_list = [cat.strip() for cat in categories.split(",") if cat.strip()]
        if category_list:
            expenses_df = expenses_df[expenses_df["category"].isin(category_list)]
            print(f"After category filter (expenses): {len(expenses_df)} transactions")

    # Group by category
    if "category" in expenses_df.columns:
        expenses_df["category"] = expenses_df["category"].fillna("Uncategorized")
        categories_data = expenses_df.groupby("category")["amount"].sum()

        print(f"Categories found: {categories_data.index.tolist()}")
        print(f"Category amounts: {categories_data.values.tolist()}")

        if len(categories_data) == 0:
            return {"labels": ["No Data"], "values": [0]}

        # Get top categories
        top_categories = categories_data.nlargest(5)

        # Add "Other" for the rest
        if len(categories_data) > 5:
            other_sum = categories_data.nsmallest(len(categories_data) - 5).sum()
            if other_sum > 0:
                top_categories["Other"] = other_sum

        return {
            "labels": top_categories.index.tolist(),
            "values": top_categories.values.tolist(),
        }

    # Fallback for no categories
    return {"labels": ["Uncategorized"], "values": [expenses_df["amount"].sum()]}
