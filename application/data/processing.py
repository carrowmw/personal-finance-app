from typing import Optional
import pandas as pd
from sqlalchemy import select
from application.data.models import Transaction, User
from application.frontend.src import db


def split_category(category_list: list) -> pd.Series:
    """Split category list into main category and subcategory."""
    if not category_list or len(category_list) == 0:
        return pd.Series(["Unknown", "Unknown"])
    elif len(category_list) == 1:
        return pd.Series([category_list[0], "Unknown"])


def get_transactions_df(username: str) -> Optional[pd.DataFrame]:
    """
    Get transactions for a user and convert them to a pandas DataFrame

    Args:
        username (str): Username to fetch transactions for

    Returns:
        Optional[pd.DataFrame]: DataFrame of transactions or None if no transactions
    """
    # Get user and their transactions
    user = User.query.filter_by(username=username).first()
    if not user:
        return None

    # Query transactions
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    if not transactions:
        return None

    # Convert to dictionary format for pandas
    transactions_data = [
        {
            "account_id": t.account_id,
            "amount": float(t.amount),
            "category": t.category.split("/") if t.category else ["Unknown"],
            "date": t.date,
            "iso_currency_code": "USD",  # Add more currency handling if needed
            "merchant_name": t.merchant_name,
            "name": t.name,
        }
        for t in transactions
    ]

    # Create DataFrame
    transactions_df = pd.DataFrame(transactions_data)

    # Define columns to keep
    subset_of_columns = [
        "account_id",
        "amount",
        "category",
        "date",
        "iso_currency_code",
        "merchant_name",
        "name",
    ]
    transactions_df = transactions_df[subset_of_columns]

    # Split categories
    category_df = transactions_df["category"].apply(split_category)
    category_df.columns = ["category", "subcategory"]

    # Create final DataFrame
    expanded_transactions_df = pd.concat(
        [transactions_df.drop(columns=["category"]), category_df], axis=1
    )

    return expanded_transactions_df


def get_transaction_summary(username: str) -> dict:
    """
    Get summary statistics for user's transactions

    Args:
        username (str): Username to get summary for

    Returns:
        dict: Summary statistics
    """
    df = get_transactions_df(username)
    if df is None:
        return {
            "total_transactions": 0,
            "total_spent": 0,
            "average_transaction": 0,
            "top_categories": [],
        }

    summary = {
        "total_transactions": len(df),
        "total_spent": df["amount"].sum(),
        "average_transaction": df["amount"].mean(),
        "top_categories": df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .to_dict(),
    }

    return summary


def get_monthly_spending(username: str) -> dict:
    """
    Get monthly spending totals

    Args:
        username (str): Username to get monthly spending for

    Returns:
        dict: Monthly spending totals
    """
    df = get_transactions_df(username)
    if df is None:
        return {}

    # Convert date to datetime if it isn't already
    df["date"] = pd.to_datetime(df["date"])

    monthly = (
        df.groupby(df["date"].dt.strftime("%Y-%m"))
        .agg({"amount": "sum", "name": "count"})
        .rename(columns={"name": "transaction_count"})
        .to_dict("index")
    )

    return monthly
