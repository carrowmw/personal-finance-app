# app/plaid/routes.py

from flask import jsonify, request, render_template, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.plaid import plaid_bp
from app.plaid.service import create_link_token, exchange_public_token, get_accounts
from app.plaid.utils import sync_transactions, sync_balances
from app.models import User
from app.extensions import db


@plaid_bp.route("/link", methods=["GET"])
@login_required
def plaid_link():
    """Show the Plaid Link interface."""
    # Create a link token for the current user
    link_token = create_link_token(current_user.id)

    if not link_token:
        flash(
            "Failed to initialize Plaid connection. Please try again later.", "danger"
        )
        return redirect(url_for("financial.dashboard"))

    # Store the link token in the session for safekeeping
    session["link_token"] = link_token

    return render_template(
        "plaid/link.html", title="Connect Bank Account", link_token=link_token
    )


@plaid_bp.route("/create_link_token", methods=["GET"])
@login_required
def api_create_link_token():
    """Create a Plaid Link token."""
    link_token = create_link_token(current_user.id)

    if link_token:
        return jsonify({"link_token": link_token})
    else:
        return jsonify({"error": "Failed to create link token"}), 500


@plaid_bp.route("/exchange_public_token", methods=["POST"])
@login_required
def api_exchange_public_token():
    """Exchange a public token for an access token."""
    public_token = request.form.get("public_token")

    if not public_token:
        flash("No public token received from Plaid", "danger")
        return redirect(url_for("financial.dashboard"))

    access_token = exchange_public_token(public_token)

    if access_token:
        # Store the access token with the user
        current_user.access_token = access_token
        db.session.commit()

        # Sync initial data
        success = sync_initial_data(current_user)

        if success:
            flash("Your bank account was successfully connected!", "success")
        else:
            flash(
                "Your bank account was connected, but we couldn't fetch your data. Please try refreshing later.",
                "warning",
            )

        return redirect(url_for("financial.dashboard"))
    else:
        flash("Failed to connect your bank account. Please try again.", "danger")
        return redirect(url_for("plaid.plaid_link"))


@plaid_bp.route("/success", methods=["GET", "POST"])
@login_required
def plaid_success():
    """Handle successful Plaid Link."""
    if request.method == "POST":
        public_token = request.form.get("public_token")
        if public_token:
            return api_exchange_public_token()

    return redirect(url_for("financial.dashboard"))


@plaid_bp.route("/sync_data", methods=["POST"])
@login_required
def sync_data():
    """Manually sync transactions and balances."""
    if not current_user.access_token:
        flash("No connected bank account found.", "warning")
        return redirect(url_for("financial.dashboard"))

    success = sync_initial_data(current_user)

    if success:
        flash("Your financial data has been refreshed!", "success")
    else:
        flash(
            "Failed to refresh your financial data. Please try again later.", "danger"
        )

    return redirect(url_for("financial.dashboard"))


def sync_initial_data(user):
    """Sync transactions and balances for a newly connected account."""
    try:
        # First sync balances to get account information
        balances_result, balances_success = sync_balances(user)

        if not balances_success:
            return False

        # Then sync transactions
        transactions_result, transactions_success = sync_transactions(user)

        return transactions_success
    except Exception as e:
        print(f"Error syncing initial data: {e}")
        return False
