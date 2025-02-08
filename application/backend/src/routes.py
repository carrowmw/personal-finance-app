# application/backend/src/routes.py

from datetime import datetime
from decimal import Decimal
from flask import Blueprint, request, jsonify, Response
from flask_cors import CORS
import plaid
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest

from application.data.processing import (
    get_transactions_df,
    get_transaction_summary,
    get_monthly_spending,
)

from application.frontend.src import db
from application.data.models import User, Transaction, Balance
from application.backend.src.plaid_service import (
    create_link_token,
    exchange_public_token,
    initialize_plaid_client,
)
from application.backend.src.utils import format_error
from application.backend.src.config import BackendConfig as Config

# Load environment variables
Config.validate()
PLAID_USER_ID = Config.PLAID_USER_ID
PLAID_COUNTRY_CODES = Config.PLAID_COUNTRY_CODES
PLAID_PRODUCTS = Config.PLAID_PRODUCTS
PLAID_REDIRECT_URI = Config.PLAID_REDIRECT_URI
ALLOWED_ORIGINS = Config.ALLOWED_ORIGINS


backend = Blueprint("backend", __name__)

CORS(
    backend,
    resources={r"/api/*": {"origins": ALLOWED_ORIGINS}},
)


# Initialize Plaid client
client = initialize_plaid_client()


@backend.route("/api/check_access_token", methods=["GET"])
def check_access_token(username):
    user = User.query.filter_by(username=username).first_or_404()
    access_token = user.access_token
    if access_token:
        return jsonify({"access_token": access_token})
    else:
        return jsonify({"error": "No access token found"}), 404


@backend.route("/api/create_link_token", methods=["GET"])
def api_create_link_token():
    link_token = create_link_token(
        client, PLAID_USER_ID, PLAID_COUNTRY_CODES, PLAID_PRODUCTS
    )
    if link_token:
        print(f"Successfully created link token: {link_token}")
        return jsonify({"link_token": link_token})
    else:
        return jsonify({"error": "Failed to create link token"}), 500


@backend.route("/api/exchange_public_token", methods=["POST"])
def api_exchange_public_token(username):
    public_token = request.json.get("public_token")
    if not public_token:
        return jsonify({"error": "Please provide a public token"}), 400

    print(f"Exchanging public token: {public_token}")
    access_token = exchange_public_token(client, public_token)
    if access_token:
        print(f"Successfully exchanged public token for access token: {access_token}")
        user = User.query.filter_by(username=username).first_or_404()
        user.access_token = access_token
        return jsonify({"access_token": access_token})
    else:
        return (
            jsonify({"error": "Failed to exchange public token for access token"}),
            500,
        )


@backend.route("/api/transactions", methods=["POST"])
def api_get_transactions(username):
    user = User.query.filter_by(username=username).first_or_404()
    access_token = user.access_token
    if not access_token:
        return (
            jsonify(
                {"error": "No access token available. Please connect your account."}
            ),
            400,
        )

    cursor = user.cursor

    added = []
    modified = []
    removed = []  # Removed transaction ids
    has_more = True

    try:
        while has_more:
            response = TransactionsSyncRequest(
                access_token=access_token,
                cursor=cursor,
            )
            response = client.transactions_sync(response).to_dict()
            cursor = response["next_cursor"]
            user.cursor = cursor

            added.extend(response["added"])
            modified.extend(response["modified"])
            removed.extend(response["removed"])
            has_more = response["has_more"]

        # Handle removed transactions
        if removed:
            Transaction.query.filter(
                Transaction.plaid_transaction_id.in_(
                    t["transaction_id"] for t in removed
                )
            ).delete(synchronize_session=False)

        # Handle modified transactions
        for t in modified:
            existing_transaction = Transaction.query.filter_by(
                plaid_transaction_id=t["transaction_id"]
            ).first()
            if existing_transaction:
                existing_transaction.amount = t["amount"]
                existing_transaction.name = t["name"]
                existing_transaction.merchant_name = t.get("merchant_name")
                existing_transaction.pending = t["pending"]
                existing_transaction.category = (
                    t["category"][-1] if t.get("category") else None
                )
                existing_transaction.category_id = t.get("category_id")

        # Handle new transactions
        new_transactions = []
        for t in added:
            # Check if transaction already exists (just in case)
            existing_transaction = Transaction.query.filter_by(
                plaid_transaction_id=t["transaction_id"]
            ).first()

            if new_transactions:
                db.session.bulk_save_objects(new_transactions)

        # Commit all changes to database
        db.session.commit()

        # Get the 8 most recent transactions
        latest_transactions = (
            Transaction.query.filter_by(user_id=user.id)
            .order_by(Transaction.date.desc())
            .limit(8)
            .all()
        )

        # Convert to dictionary format for JSON response
        transactions_response = [
            {
                "transaction_id": t.plaid_transaction_id,
                "date": t.date.strftime("%Y-%m-%d"),
                "name": t.name,
                "amount": float(t.amount),
                "category": t.category,
                "merchant_name": t.merchant_name,
                "pending": t.pending,
            }
            for t in latest_transactions
        ]

        return jsonify({"latest_transactions": transactions_response})

    except plaid.ApiException as e:
        error_response = format_error(e)
        return jsonify(error_response)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@backend.route("/api/transactions/analysis", methods=["GET"])
def transaction_analysis(username):
    """Route for getting transaction analysis"""
    try:
        df = get_transactions_df(username)
        if df is None:
            return jsonify({"error": "No transactions found"}), 404

        summary = get_transaction_summary(username)
        monthly = get_monthly_spending(username)

        return jsonify(
            {"summary": summary, "monthly_spending": monthly, "success": True}
        )

    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


@backend.route("/api/transactions/download", methods=["GET"])
def download_transactions(username):
    """Route for downloading transactions as CSV"""
    try:
        df = get_transactions_df(username)
        if df is None:
            return jsonify({"error": "No transactions found"}), 404

        # Convert DataFrame to CSV
        csv_data = df.to_csv(index=False)

        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-disposition": f"attachment; filename=transactions_{username}.csv"
            },
        )

    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


@backend.route("/api/balance", methods=["POST"])
def api_get_balance(username):
    user = User.query.filter_by(username=username).first_or_404()
    access_token = user.access_token

    if not access_token:
        return (
            jsonify(
                {"error": "No access token available. Please connect your account."}
            ),
            400,
        )

    try:
        # Get balance from Plaid
        request = AccountsBalanceGetRequest(access_token=access_token)
        response = client.accounts_balance_get(request).to_dict()

        # Process each account
        accounts = response["accounts"]
        updated_accounts = []

        for account_data in accounts:
            # Check if account already exists
            existing_balance = Balance.query.filter_by(
                plaid_account_id=account_data["account_id"]
            ).first()

            if existing_balance:
                # Update existing account
                existing_balance.current_balance = (
                    Decimal(str(account_data["balances"]["current"]))
                    if account_data["balances"]["current"] is not None
                    else Decimal("0")
                )
                existing_balance.available_balance = (
                    Decimal(str(account_data["balances"]["available"]))
                    if account_data["balances"]["available"] is not None
                    else None
                )
                existing_balance.limit = (
                    Decimal(str(account_data["balances"]["limit"]))
                    if account_data["balances"].get("limit")
                    else None
                )
                existing_balance.name = account_data["name"]
                existing_balance.official_name = account_data.get("official_name")
                existing_balance.type = account_data["type"]
                existing_balance.subtype = account_data.get("subtype")
                existing_balance.last_updated = datetime.utcnow()
                updated_accounts.append(existing_balance)
            else:
                # Create new account balance
                new_balance = Balance.from_plaid_account(account_data, user.id)
                db.session.add(new_balance)
                updated_accounts.append(new_balance)

        # Commit changes
        db.session.commit()

        # Format response
        response_data = {
            "accounts": [
                {
                    "account_id": account.plaid_account_id,
                    "name": account.name,
                    "official_name": account.official_name,
                    "type": account.type,
                    "subtype": account.subtype,
                    "balances": {
                        "current": float(account.current_balance),
                        "available": (
                            float(account.available_balance)
                            if account.available_balance is not None
                            else None
                        ),
                        "limit": (
                            float(account.limit) if account.limit is not None else None
                        ),
                        "iso_currency_code": account.iso_currency_code,
                    },
                    "last_updated": account.last_updated.isoformat(),
                }
                for account in updated_accounts
            ]
        }

        return jsonify(response_data)

    except plaid.ApiException as e:
        error_response = format_error(e)
        return jsonify(error_response)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Additional helper route to get balances without refreshing from Plaid
@backend.route("/api/balance/cached", methods=["GET"])
def get_cached_balance(username):
    try:
        user = User.query.filter_by(username=username).first_or_404()

        # Get latest balances from database
        balances = Balance.query.filter_by(user_id=user.id).all()

        if not balances:
            return (
                jsonify(
                    {"error": "No balance information found. Please refresh balances."}
                ),
                404,
            )

        response_data = {
            "accounts": [
                {
                    "account_id": balance.plaid_account_id,
                    "name": balance.name,
                    "official_name": balance.official_name,
                    "type": balance.type,
                    "subtype": balance.subtype,
                    "balances": {
                        "current": float(balance.current_balance),
                        "available": (
                            float(balance.available_balance)
                            if balance.available_balance is not None
                            else None
                        ),
                        "limit": (
                            float(balance.limit) if balance.limit is not None else None
                        ),
                        "iso_currency_code": balance.iso_currency_code,
                    },
                    "last_updated": balance.last_updated.isoformat(),
                }
                for balance in balances
            ]
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
