# app/models.py

"""
Unified set of models.
"""

from datetime import datetime
from decimal import Decimal
from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
from app.extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = "user"  # Explicitly declare table name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default="default.jpg")
    password = db.Column(db.String(60), nullable=False)
    access_token = db.Column(db.String(120), nullable=True)
    cursor = db.Column(db.String(120), nullable=True)
    posts = db.relationship("Post", backref="author", lazy=True)
    transactions = db.relationship("Transaction", backref="user", lazy=True)
    balances = db.relationship("Balance", backref="user", lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return s.dumps({"user_id": self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            user_id = s.loads(token, max_age=expires_sec)["user_id"]
            return User.query.get(user_id)
        except:
            return None

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


# Add the rest of your models (Post, Transaction, Balance) here


class Post(db.Model):
    __tablename__ = "post"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"


class Transaction(db.Model):
    __tablename__ = "transaction"
    id = db.Column(db.Integer, primary_key=True)
    plaid_transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Transaction details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    merchant_name = db.Column(db.String(200))
    category = db.Column(db.String(100))
    category_id = db.Column(db.String(100))
    pending = db.Column(db.Boolean, default=False)

    # Account information
    account_id = db.Column(db.String(100), nullable=False)
    account_name = db.Column(db.String(100))

    # Payment details
    payment_channel = db.Column(db.String(50))
    authorized_date = db.Column(db.DateTime)

    # Additional metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Factory method
    @staticmethod
    def from_plaid_transaction(plaid_transaction, user_id):
        """Create a Transaction from Plaid data"""
        # Handle the date field, which may be a string or datetime object
        transaction_date = plaid_transaction["date"]
        if isinstance(transaction_date, str):
            date_obj = datetime.strptime(transaction_date, "%Y-%m-%d").date()
        else:
            date_obj = transaction_date

        # Handle authorized_date similarly
        authorized_date = plaid_transaction.get("authorized_date")
        if authorized_date:
            if isinstance(authorized_date, str):
                authorized_date_obj = datetime.strptime(
                    authorized_date, "%Y-%m-%d"
                ).date()
            else:
                authorized_date_obj = authorized_date
        else:
            authorized_date_obj = None

        # Handle amount (Plaid reports expenses as positive values and income as negative)
        amount = Decimal(str(plaid_transaction["amount"]))

        # Extract account name if available
        account_name = plaid_transaction.get("account_name")

        # Extract category and properly handle nested categories
        category = None
        if plaid_transaction.get("category"):
            if (
                isinstance(plaid_transaction["category"], list)
                and len(plaid_transaction["category"]) > 0
            ):
                # Get the most specific category (last item in the list)
                category = plaid_transaction["category"][-1]
            else:
                category = plaid_transaction.get("category")

        return Transaction(
            plaid_transaction_id=plaid_transaction["transaction_id"],
            user_id=user_id,
            amount=amount,
            date=date_obj,
            name=plaid_transaction["name"],
            merchant_name=plaid_transaction.get("merchant_name"),
            category=category,
            category_id=plaid_transaction.get("category_id"),
            pending=plaid_transaction.get("pending", False),
            account_id=plaid_transaction["account_id"],
            account_name=account_name,
            payment_channel=plaid_transaction.get("payment_channel"),
            authorized_date=authorized_date_obj,
        )

    def to_dict(self):
        """Convert Transaction to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "plaid_transaction_id": self.plaid_transaction_id,
            "amount": float(self.amount),
            "date": self.date.strftime("%Y-%m-%d"),
            "name": self.name,
            "merchant_name": self.merchant_name,
            "category": self.category,
            "pending": self.pending,
            "account_id": self.account_id,
            "account_name": self.account_name,
        }


class Balance(db.Model):
    __tablename__ = "balance"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Account information
    plaid_account_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    official_name = db.Column(db.String(200))
    type = db.Column(db.String(50), nullable=False)
    subtype = db.Column(db.String(50))

    # Balance information
    current_balance = db.Column(db.Numeric(10, 2), nullable=False)
    available_balance = db.Column(db.Numeric(10, 2))
    limit = db.Column(db.Numeric(10, 2))
    iso_currency_code = db.Column(db.String(3), default="USD")

    # Metadata
    last_updated = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Factory method
    @staticmethod
    def from_plaid_account(account_data, user_id):
        """Create a Balance from Plaid data"""
        return Balance(
            user_id=user_id,
            plaid_account_id=account_data["account_id"],
            name=account_data["name"],
            official_name=account_data.get("official_name"),
            type=account_data["type"],
            subtype=account_data.get("subtype"),
            current_balance=(
                Decimal(str(account_data["balances"]["current"]))
                if account_data["balances"]["current"] is not None
                else Decimal("0")
            ),
            available_balance=(
                Decimal(str(account_data["balances"]["available"]))
                if account_data["balances"].get("available") is not None
                else None
            ),
            limit=(
                Decimal(str(account_data["balances"]["limit"]))
                if account_data["balances"].get("limit") is not None
                else None
            ),
            iso_currency_code=account_data["balances"].get("iso_currency_code", "USD"),
        )

    def to_dict(self):
        """Convert Balance to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "plaid_account_id": self.plaid_account_id,
            "name": self.name,
            "official_name": self.official_name,
            "type": self.type,
            "subtype": self.subtype,
            "current_balance": float(self.current_balance),
            "available_balance": (
                float(self.available_balance) if self.available_balance else None
            ),
            "limit": float(self.limit) if self.limit else None,
            "iso_currency_code": self.iso_currency_code,
            "last_updated": (
                self.last_updated.isoformat() if self.last_updated else None
            ),
        }
