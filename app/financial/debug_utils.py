# Add this function to app/financial/debug_utils.py

from app.models import Transaction, User
import pandas as pd
from datetime import datetime, timedelta
from app.models import User, Transaction
from app.financial.services import (
    get_transactions_df,
    get_spending_by_category,
    calculate_monthly_spending,
)
from app.models import User, Transaction
from app.extensions import db


def debug_transactions(username=None, user_id=None):
    """Print debug information about transactions in the database."""
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            user_id = user.id
        else:
            print(f"User '{username}' not found")
            return

    if user_id:
        # Get basic transaction count
        transactions = Transaction.query.filter_by(user_id=user_id).all()
        print(f"Found {len(transactions)} transactions for user_id {user_id}")

        if len(transactions) > 0:
            # Check date range
            dates = [t.date for t in transactions]
            min_date = min(dates)
            max_date = max(dates)
            print(f"Date range: {min_date} to {max_date}")

            # Check amount range
            amounts = [float(t.amount) for t in transactions]
            min_amount = min(amounts)
            max_amount = max(amounts)
            avg_amount = sum(amounts) / len(amounts)
            print(
                f"Amount range: {min_amount} to {max_amount}, average: {avg_amount:.2f}"
            )

            # Count positive and negative transactions
            pos_count = sum(1 for a in amounts if a > 0)
            neg_count = sum(1 for a in amounts if a < 0)
            print(f"Positive (spending) transactions: {pos_count}")
            print(f"Negative (income) transactions: {neg_count}")

            # Check categories
            categories = {}
            for t in transactions:
                cat = t.category or "Uncategorized"
                if cat in categories:
                    categories[cat] += 1
                else:
                    categories[cat] = 1

            print(f"Found {len(categories)} unique categories")
            top_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
            print("Top 5 categories:")
            for cat, count in top_cats:
                print(f"  - {cat}: {count} transactions")

            # Check current month transactions
            current_month = datetime.now().replace(day=1).date()

            # Fix: Convert transaction date to date type for comparison if it's a datetime
            current_txns = [
                t
                for t in transactions
                if (t.date.date() if hasattr(t.date, "date") else t.date)
                >= current_month
            ]
            print(f"Current month transactions: {len(current_txns)}")

            # Get total spending for current month
            current_spending = sum(
                float(t.amount) for t in current_txns if float(t.amount) > 0
            )
            print(f"Current month spending: £{current_spending:.2f}")

            # Check last 6 months of data for monthly chart
            six_months_ago = (datetime.now() - timedelta(days=180)).date()
            # Fix the date comparison here too
            last_6m_txns = [
                t
                for t in transactions
                if (t.date.date() if hasattr(t.date, "date") else t.date)
                >= six_months_ago
            ]
            print(f"Last 6 months transactions: {len(last_6m_txns)}")
    else:
        print("No user specified for transaction debugging")


def fix_transaction_data(username=None):
    """Fix potential data issues in transactions."""
    if username:
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"User '{username}' not found")
            return
        user_id = user.id
    else:
        print("No username provided, fixing all transactions")
        user_id = None

    # Get transactions
    if user_id:
        transactions = Transaction.query.filter_by(user_id=user_id).all()
    else:
        transactions = Transaction.query.all()

    print(f"Found {len(transactions)} transactions to process")

    # Count transactions with issues
    missing_category = 0
    list_category = 0
    null_category = 0
    updated_count = 0

    # Fix each transaction
    for transaction in transactions:
        updated = False

        # Fix categories that are stored as lists
        if transaction.category and isinstance(transaction.category, str):
            if transaction.category.startswith("[") and transaction.category.endswith(
                "]"
            ):
                try:
                    import json

                    cat_list = json.loads(transaction.category)
                    if isinstance(cat_list, list) and len(cat_list) > 0:
                        transaction.category = cat_list[
                            -1
                        ]  # Get most specific category
                        list_category += 1
                        updated = True
                except:
                    pass

        # Fix null categories
        if transaction.category is None:
            null_category += 1
            transaction.category = "Uncategorized"
            updated = True

        # Fix missing categories
        if transaction.category == "":
            missing_category += 1
            transaction.category = "Uncategorized"
            updated = True

        if updated:
            updated_count += 1

    # Commit changes
    if updated_count > 0:
        try:
            db.session.commit()
            print(
                f"Fixed transactions: {missing_category} missing categories, {list_category} list categories, {null_category} null categories"
            )
        except Exception as e:
            db.session.rollback()
            print(f"Error committing changes: {str(e)}")
    else:
        print("No transaction fixes needed")


def inspect_chart_data(username):
    """Inspect the chart data for a user."""

    user = User.query.filter_by(username=username).first()
    if not user:
        print(f"User '{username}' not found")
        return

    # Get transactions directly from database
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    print(f"Found {len(transactions)} transactions in database")

    # Check if any transactions exist
    if len(transactions) == 0:
        print("No transactions found for this user")
        return

    # Check transaction data
    pos_amounts = sum(1 for t in transactions if float(t.amount) > 0)
    neg_amounts = sum(1 for t in transactions if float(t.amount) < 0)
    print(f"Positive amounts (expenses): {pos_amounts}")
    print(f"Negative amounts (income): {neg_amounts}")

    # Get dataframe and check it
    df = get_transactions_df(username)
    if df is None:
        print("get_transactions_df returned None")
        return

    print(f"DataFrame contains {len(df)} rows")

    if len(df) > 0:
        print(f"DataFrame columns: {df.columns.tolist()}")
        print(f"Sample data: {df.head(2).to_dict('records')}")

        # Check for amount column
        if "amount" in df.columns:
            pos_df = df[df["amount"] > 0]
            print(f"Positive amounts in DataFrame: {len(pos_df)}")

            # Check for category column
            if "category" in df.columns:
                categories = df["category"].value_counts().to_dict()
                print(
                    f"Top categories: {dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5])}"
                )
            else:
                print("No 'category' column in DataFrame")
        else:
            print("No 'amount' column in DataFrame")

    # Check monthly data
    monthly_data = calculate_monthly_spending(username, with_details=True)
    print(f"Monthly data: {monthly_data}")

    # Check category data
    category_data = get_spending_by_category(username)
    print(f"Category data: {category_data}")

    # Check data for last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    recent_txns = [
        t for t in transactions if t.date >= start_date and t.date <= end_date
    ]
    print(f"Transactions in last 30 days: {len(recent_txns)}")

    # Count positive amounts in recent transactions
    recent_pos = sum(1 for t in recent_txns if float(t.amount) > 0)
    print(f"Expenses in last 30 days: {recent_pos}")

    # Check categories in recent transactions
    recent_cats = {}
    for t in recent_txns:
        if t.category:
            cat = t.category
            if cat in recent_cats:
                recent_cats[cat] += 1
            else:
                recent_cats[cat] = 1

    print(f"Categories in last 30 days: {recent_cats}")
