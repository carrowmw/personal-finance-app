# app/plaid/utils.py

import plaid
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from decimal import Decimal
from datetime import datetime
from flask import current_app
from app.models import Transaction, Balance
from app.extensions import db


def format_error(e):
    """Format Plaid API error responses."""
    if isinstance(e, plaid.ApiException):
        response = e.body
        if hasattr(response, "json"):
            response = response.json()
        elif isinstance(response, str):
            try:
                import json

                response = json.loads(response)
            except:
                return {"error": str(e)}

        return {
            "error": {
                "status_code": e.status,
                "display_message": response.get("error_message", str(e)),
                "error_code": response.get("error_code", "UNKNOWN"),
                "error_type": response.get("error_type", "API_ERROR"),
            }
        }
    return {"error": str(e)}


def sync_transactions(user):
    """Sync transactions for a user from Plaid."""
    from app.plaid.service import initialize_plaid_client

    if not user.access_token:
        return {"error": "No access token available"}, False

    client = initialize_plaid_client()
    if not client:
        return {"error": "Failed to initialize Plaid client"}, False

    cursor = user.cursor
    added = []
    modified = []
    removed = []
    has_more = True

    try:
        # First sync call - don't use cursor parameter at all for the first request
        if not cursor:
            try:
                # Make initial sync request WITHOUT cursor parameter
                request = TransactionsSyncRequest(access_token=user.access_token)
                response = client.transactions_sync(request)
                response_dict = response.to_dict()

                # Save the cursor for future syncs
                cursor = response_dict["next_cursor"]
                user.cursor = cursor
                db.session.commit()

                # Collect initial results
                added.extend(response_dict["added"])
                modified.extend(response_dict["modified"])
                removed.extend([r["transaction_id"] for r in response_dict["removed"]])
                has_more = response_dict["has_more"]

                current_app.logger.info(
                    f"Initial sync successful, got cursor: {cursor}"
                )
            except Exception as e:
                current_app.logger.error(f"Error initializing cursor: {e}")
                return {"error": str(e)}, False

        # Continue syncing if has_more is True and we have a cursor
        while has_more and cursor:
            request = TransactionsSyncRequest(
                access_token=user.access_token, cursor=cursor
            )
            response = client.transactions_sync(request)
            response_dict = response.to_dict()

            # Update cursor
            cursor = response_dict["next_cursor"]
            user.cursor = cursor

            # Collect results
            added.extend(response_dict["added"])
            modified.extend(response_dict["modified"])
            removed.extend([r["transaction_id"] for r in response_dict["removed"]])
            has_more = response_dict["has_more"]

        # Process removed transactions
        if removed:
            Transaction.query.filter(
                Transaction.plaid_transaction_id.in_(removed)
            ).delete(synchronize_session=False)

        # Process modified transactions
        for t in modified:
            transaction = Transaction.query.filter_by(
                plaid_transaction_id=t["transaction_id"]
            ).first()

            if transaction:
                transaction.amount = Decimal(str(t["amount"]))
                transaction.name = t["name"]
                transaction.merchant_name = t.get("merchant_name")
                transaction.pending = t["pending"]
                transaction.category = (
                    t.get("category", ["Unknown"])[-1] if t.get("category") else None
                )
                transaction.category_id = t.get("category_id")

        # Process added transactions
        for t in added:
            # Check if transaction already exists
            exists = Transaction.query.filter_by(
                plaid_transaction_id=t["transaction_id"]
            ).first()

            if not exists:
                new_transaction = Transaction.from_plaid_transaction(t, user.id)
                db.session.add(new_transaction)

        # Commit changes
        db.session.commit()

        # Diagnostic code
        current_app.logger.info(
            f"Successfully processed transactions: {len(added)} added, {len(modified)} modified, {len(removed)} removed"
        )
        if added:
            sample = added[0]
            current_app.logger.info(
                f"Sample transaction: {sample['name']}, Amount: {sample['amount']}, Date: {sample['date']}"
            )

        return {
            "success": True,
            "added": len(added),
            "modified": len(modified),
            "removed": len(removed),
        }, True

    except plaid.ApiException as e:
        db.session.rollback()
        current_app.logger.error(f"Plaid API error in sync_transactions: {e}")
        return format_error(e), False
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error in sync_transactions: {e}")
        return {"error": str(e)}, False


def sync_balances(user):
    """Sync account balances for a user from Plaid."""
    from app.plaid.service import initialize_plaid_client

    if not user.access_token:
        return {"error": "No access token available"}, False

    client = initialize_plaid_client()
    if not client:
        return {"error": "Failed to initialize Plaid client"}, False

    try:
        request = AccountsBalanceGetRequest(access_token=user.access_token)
        response = client.accounts_balance_get(request).to_dict()

        accounts = response["accounts"]
        updated_accounts = []

        for account_data in accounts:
            # Check if account already exists
            balance = Balance.query.filter_by(
                plaid_account_id=account_data["account_id"]
            ).first()

            if balance:
                # Update existing account
                balance.current_balance = (
                    Decimal(str(account_data["balances"]["current"]))
                    if account_data["balances"]["current"] is not None
                    else Decimal("0")
                )
                balance.available_balance = (
                    Decimal(str(account_data["balances"]["available"]))
                    if account_data["balances"].get("available") is not None
                    else None
                )
                balance.limit = (
                    Decimal(str(account_data["balances"]["limit"]))
                    if account_data["balances"].get("limit") is not None
                    else None
                )
                balance.name = account_data["name"]
                balance.official_name = account_data.get("official_name")
                balance.type = account_data["type"]
                balance.subtype = account_data.get("subtype")
                balance.last_updated = datetime.utcnow()
                updated_accounts.append(balance)
            else:
                # Create new account balance
                new_balance = Balance.from_plaid_account(account_data, user.id)
                db.session.add(new_balance)
                updated_accounts.append(new_balance)

        # Commit changes
        db.session.commit()

        return {
            "success": True,
            "accounts": [account.plaid_account_id for account in updated_accounts],
        }, True

    except plaid.ApiException as e:
        db.session.rollback()
        current_app.logger.error(f"Plaid API error in sync_balances: {e}")
        return format_error(e), False
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error in sync_balances: {e}")
        return {"error": str(e)}, False
