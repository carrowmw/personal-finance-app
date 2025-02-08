# application/data/models.py
from datetime import datetime
from decimal import Decimal
from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from application.frontend.src import (
    db,
    login_manager,
)  # import app for the app secret key


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default="default.png")
    password = db.Column(db.String(60), nullable=False)
    access_token = db.Column(db.String(120), nullable=True)
    cursor = db.Column(db.String(120), nullable=True)
    posts = db.relationship("Post", backref="author", lazy=True)
    transactions = db.relationship("Transactions", backref="author")
    balance = db.relationship("Balance", backref="author")

    # Generate a token for the user
    def get_reset_token(self, expires_sec=1800):
        print("Debug - Before Serializer:")
        print(f"Secret Key Type: {type(current_app.config['SECRET_KEY'])}")
        print(f"Secret Key Value: {current_app.config['SECRET_KEY']}")

        try:
            s = Serializer(
                secret_key=current_app.config["APP_SECRET_KEY"],
                salt="reset-password",  # typically a rondom string would go here
                signer_kwargs={"key_derivation": "hmac"},
            )

            token = s.dumps({"user_id": self.id})
            print("Generated Token: {token}")
            return token
        except Exception as e:
            print(f"Error in token generation: {str(e)}")
            raise

    @staticmethod  # This is a static method, it does not take self as an argument
    # Verify the token
    def verify_reset_token(token):
        print("Debug - Token Verification:")
        print(f"Received Token: {token}")

        try:
            s = Serializer(
                secret_key=current_app.config["APP_SECRET_KEY"],
                salt="reset-password",  # typically a rondom string would go here (needs to be same as above)
                signer_kwargs={"key_derivation": "hmac"},
            )
            user_id = s.loads(token, max_age=1800)["user_id"]
            print(f"Decoded user_id: {user_id}")
            return User.query.get(user_id)
        except Exception as e:
            print(f"Token verification error: {str(e)}")
            return None

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


# typically a rondom string would go here


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now())
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"


class Transaction(db.Model):
    __tablename__ = "transactions"

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

    def __repr__(self):
        return f"Transaction('{self.name}', ${self.amount}, {self.date})"

    @staticmethod
    def from_plaid_transaction(plaid_transaction, user_id):
        """
        Convert a Plaid transaction to our Transaction model
        """
        return Transaction(
            plaid_transaction_id=plaid_transaction["transaction_id"],
            user_id=user_id,
            amount=Decimal(str(plaid_transaction["amount"])),
            date=datetime.strptime(plaid_transaction["date"], "%Y-%m-%d"),
            name=plaid_transaction["name"],
            merchant_name=plaid_transaction.get("merchant_name"),
            category=(
                plaid_transaction["category"][-1]
                if plaid_transaction.get("category")
                else None
            ),
            category_id=plaid_transaction.get("category_id"),
            pending=plaid_transaction["pending"],
            account_id=plaid_transaction["account_id"],
            account_name=plaid_transaction.get("account_name"),
            payment_channel=plaid_transaction.get("payment_channel"),
            authorized_date=(
                datetime.strptime(plaid_transaction["authorized_date"], "%Y-%m-%d")
                if plaid_transaction.get("authorized_date")
                else None
            ),
        )


def save_plaid_transactions(transactions_data, user_id):
    """
    Save or update transactions from Plaid API response

    Args:
        transactions_data (list): List of transaction dictionaries from Plaid
        user_id (int): ID of the user who owns these transactions
    """
    new_transactions = []
    updated_count = 0

    for plaid_transaction in transactions_data:
        # Check if transaction already exists
        existing_transaction = Transaction.query.filter_by(
            plaid_transaction_id=plaid_transaction["transaction_id"]
        ).first()

        if existing_transaction:
            # Update existing transaction
            existing_transaction.amount = Decimal(str(plaid_transaction["amount"]))
            existing_transaction.name = plaid_transaction["name"]
            existing_transaction.merchant_name = plaid_transaction.get("merchant_name")
            existing_transaction.pending = plaid_transaction["pending"]
            updated_count += 1
        else:
            # Create new transaction
            new_transaction = Transaction.from_plaid_transaction(
                plaid_transaction, user_id
            )
            new_transactions.append(new_transaction)

    if new_transactions:
        db.session.bulk_save_objects(new_transactions)

    try:
        db.session.commit()
        return len(new_transactions), updated_count
    except Exception as e:
        db.session.rollback()
        raise e


class Balance(db.Model):
    __tablename__ = "balances"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Account information
    account_id = db.Column(db.String(100), nullable=False)
    plaid_account_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    official_name = db.Column(db.String(200))
    type = db.Column(db.String(50), nullable=False)
    subtype = db.Column(db.String(50))

    # Balance information
    current_balance = db.Column(db.Numeric(10, 2), nullable=False)
    available_balance = db.Column(db.Numeric(10, 2))
    limit = db.Column(db.Numeric(10, 2))
    iso_currency_code = db.Column(db.String(3))

    # Metadata
    last_updated = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"Balance('{self.name}', Current: ${self.current_balance}, Available: ${self.available_balance})"

    @staticmethod
    def from_plaid_account(account_data, user_id):
        """
        Create a Balance instance from Plaid account data
        """
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
                if account_data["balances"]["available"] is not None
                else None
            ),
            limit=(
                Decimal(str(account_data["balances"]["limit"]))
                if account_data["balances"].get("limit")
                else None
            ),
            iso_currency_code=account_data["balances"].get("iso_currency_code", "USD"),
        )
