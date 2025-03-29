from decimal import Decimal
import pandas as pd
import json


def format_currency(amount):
    """Format a decimal amount as currency."""
    return f"£{float(amount):,.2f}"


def to_dict(obj):
    """Convert a SQLAlchemy model instance to a dictionary."""
    if hasattr(obj, "__table__"):
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    return obj


def parse_plaid_transaction(plaid_transaction, user_id):
    """Parse a Plaid transaction into a standardized format."""
    from app.models import Transaction
    from datetime import datetime

    return Transaction(
        plaid_transaction_id=plaid_transaction["transaction_id"],
        user_id=user_id,
        amount=Decimal(str(plaid_transaction["amount"])),
        date=datetime.strptime(plaid_transaction["date"], "%Y-%m-%d"),
        name=plaid_transaction["name"],
        merchant_name=plaid_transaction.get("merchant_name"),
        category=(
            plaid_transaction.get("category", ["Unknown"])[-1]
            if plaid_transaction.get("category")
            else None
        ),
        category_id=plaid_transaction.get("category_id"),
        pending=plaid_transaction.get("pending", False),
        account_id=plaid_transaction["account_id"],
        account_name=plaid_transaction.get("account_name"),
        payment_channel=plaid_transaction.get("payment_channel"),
        authorized_date=(
            datetime.strptime(plaid_transaction["authorized_date"], "%Y-%m-%d")
            if plaid_transaction.get("authorized_date")
            else None
        ),
    )


def transactions_to_csv(transactions):
    """Convert transactions to CSV format."""
    # Convert to list of dictionaries
    data = [
        {
            "date": t.date.strftime("%Y-%m-%d"),
            "name": t.name,
            "merchant": t.merchant_name or "",
            "category": t.category or "Uncategorized",
            "amount": float(t.amount),
            "account": t.account_name or t.account_id,
        }
        for t in transactions
    ]

    # Create DataFrame and convert to CSV
    df = pd.DataFrame(data)
    return df.to_csv(index=False)
