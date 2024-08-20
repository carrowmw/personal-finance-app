# application/backend/src/routes.py

from flask import Blueprint, request, jsonify
from flask_cors import CORS
import plaid
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from application.backend.src.plaid_service import (
    create_link_token,
    exchange_public_token,
    initialize_plaid_client,
)
from application.backend.src.utils import (
    pretty_print_response,
    get_env_variables,
    save_access_token,
    load_access_token,
    save_cursor,
    load_cursor,
    save_transactions,
    save_balance,
    format_error,
)

backend = Blueprint("backend", __name__)
CORS(
    backend,
    resources={
        r"/api/*": {"origins": ["http://192.0.0.2:5010", "http://localhost:5010"]}
    },
)

# Load environment variables
env_vars = get_env_variables()
user_id = env_vars["PLAID_USER_ID"]
country_codes = env_vars["PLAID_COUNTRY_CODES"]
products = env_vars["PLAID_PRODUCTS"]

# Initialize Plaid client
client = initialize_plaid_client()


@backend.route("/api/check_access_token", methods=["GET"])
def check_access_token():
    access_token = load_access_token()
    if access_token:
        return jsonify({"access_token": access_token})
    else:
        return jsonify({"error": "No access token found"}), 404


@backend.route("/api/create_link_token", methods=["GET"])
def api_create_link_token():
    link_token = create_link_token(client, user_id, country_codes, products)
    if link_token:
        print(f"Successfully created link token: {link_token}")
        return jsonify({"link_token": link_token})
    else:
        return jsonify({"error": "Failed to create link token"}), 500


@backend.route("/api/exchange_public_token", methods=["POST"])
def api_exchange_public_token():
    public_token = request.json.get("public_token")
    if not public_token:
        return jsonify({"error": "Please provide a public token"}), 400

    print(f"Exchanging public token: {public_token}")
    access_token = exchange_public_token(client, public_token)
    if access_token:
        print(f"Successfully exchanged public token for access token: {access_token}")
        save_access_token(access_token)
        return jsonify({"access_token": access_token})
    else:
        return (
            jsonify({"error": "Failed to exchange public token for access token"}),
            500,
        )


@backend.route("/api/transactions", methods=["POST"])
def api_get_transactions():
    access_token = load_access_token()
    if not access_token:
        return (
            jsonify(
                {"error": "No access token available. Please connect your account."}
            ),
            400,
        )

    cursor = load_cursor()

    added = []
    modified = []
    removed = []  # Removed transaction ids
    has_more = True

    try:
        while has_more:
            request = TransactionsSyncRequest(
                access_token=access_token,
                cursor=cursor,
            )
            response = client.transactions_sync(request).to_dict()
            cursor = response["next_cursor"]
            save_cursor(cursor)

            added.extend(response["added"])
            modified.extend(response["modified"])
            removed.extend(response["removed"])
            has_more = response["has_more"]

        # Print transactions
        # pretty_print_response(added)

        # Save transactions to file
        save_transactions(added)

        # Return the 8 most recent transactions
        latest_transactions = sorted(added, key=lambda t: t["date"])[-8:]
        # print(f"Latest transactions: {latest_transactions}")
        return jsonify({"latest_transactions": latest_transactions})

    except plaid.ApiException as e:
        error_response = format_error(e)
        return jsonify(error_response)


@backend.route("/api/balance", methods=["POST"])
def api_get_balance():
    access_token = load_access_token()
    try:
        request = AccountsBalanceGetRequest(access_token=access_token)
        response = client.accounts_balance_get(request)

        # pretty_print_response(response.to_dict())
        save_balance(response.to_dict())
        return jsonify(response.to_dict())
    except plaid.ApiException as e:
        error_response = format_error(e)
        return jsonify(error_response)
