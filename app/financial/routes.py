# app/financial/routes.py
import json
from datetime import datetime, timedelta

from flask import (
    render_template,
    request,
    jsonify,
    flash,
    redirect,
    url_for,
    current_app,
)
from flask_login import login_required, current_user
from app.financial import financial_bp
from app.financial.services import (
    get_transactions,
    get_balances,
    get_transaction_summary,
    calculate_monthly_spending,
    get_spending_by_category,
    get_category_data_with_filters,
    get_monthly_data_with_filters,
)
from app.financial.visualizations import (
    create_spending_chart_html,
    create_category_chart_html,
    create_monthly_trend_json,
)
from app.financial.dash_app import (
    generate_spending_chart,
    generate_category_chart,
    get_transactions_data,
    get_category_options,
)
from app.models import Balance
from app.models import Transaction

from app.financial.debug_utils import (
    debug_transactions,
    inspect_chart_data,
    fix_transaction_data,
)


# Dashboard/Overview Route
@financial_bp.route("/")
@financial_bp.route("/dashboard")
@login_required
def dashboard():
    """Main financial dashboard with overview of all financial data."""
    try:
        # Get total balance
        balances = get_balances(current_user.id)
        total_balance = (
            sum(float(balance.current_balance) for balance in balances)
            if balances
            else 0
        )

        # Get recent transactions (limit to 5)
        transactions = get_transactions(current_user.id, limit=5)

        # Get monthly spending
        monthly_spending = calculate_monthly_spending(current_user.username)

        # Get accounts count
        accounts_count = len(balances) if balances else 0

        # Get spending by category for visualization
        spending_categories = get_spending_by_category(current_user.username)

        # Get monthly spending
        monthly_data = calculate_monthly_spending(
            current_user.username, with_details=True
        )

        # Generate chart HTML with our new functions
        category_chart_html = create_category_chart_html(spending_categories)
        spending_chart_html = create_spending_chart_html(monthly_data)

        return render_template(
            "financial/dashboard.html",
            title="Financial Dashboard",
            total_balance=total_balance,
            monthly_spending=monthly_spending,
            accounts_count=accounts_count,
            transactions=transactions,
            spending_categories=spending_categories,
            category_chart_html=category_chart_html,
            spending_chart_html=spending_chart_html,
        )
    except Exception as e:
        current_app.logger.error(f"Dashboard error: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", "danger")
        # Return a simple dashboard without charts
        return render_template(
            "financial/dashboard.html",
            title="Financial Dashboard",
            total_balance=0,
            monthly_spending=0,
            accounts_count=0,
            transactions=[],
            spending_categories=[],
            category_chart_html="<div class='text-center py-5'><p class='text-danger'>Error loading charts</p></div>",
            spending_chart_html="<div class='text-center py-5'><p class='text-danger'>Error loading charts</p></div>",
        )


@financial_bp.route("/accounts")
@login_required
def accounts():
    """Route for viewing account balances."""
    balances = get_balances(current_user.id)

    # Calculate total assets and liabilities
    assets = sum(
        float(b.current_balance)
        for b in balances
        if b.type in ["depository", "investment"] and b.current_balance > 0
    )
    liabilities = sum(
        float(b.current_balance)
        for b in balances
        if b.type in ["credit", "loan"] and b.current_balance > 0
    )

    return render_template(
        "financial/accounts.html",
        title="Accounts",
        balances=balances,
        assets=assets,
        liabilities=liabilities,
    )


@financial_bp.route("/transactions")
@login_required
def transactions():
    """Route for viewing transactions."""
    # Default to last 30 days if no dates provided
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    # Get date range from query params if provided
    if "start_date" in request.args and "end_date" in request.args:
        try:
            start_date = datetime.strptime(
                request.args.get("start_date"), "%Y-%m-%d"
            ).date()
            end_date = datetime.strptime(
                request.args.get("end_date"), "%Y-%m-%d"
            ).date()
        except ValueError:
            flash("Invalid date format. Using default range.", "warning")

    # Get transactions
    transactions = get_transactions(current_user.id, start_date, end_date)

    # Get account information for filtering
    accounts = get_balances(current_user.id)
    account_options = [(account.plaid_account_id, account.name) for account in accounts]

    # Calculate totals
    total_spend = sum(float(t.amount) for t in transactions if float(t.amount) > 0)
    total_income = sum(
        abs(float(t.amount)) for t in transactions if float(t.amount) < 0
    )

    return render_template(
        "financial/transactions.html",
        title="Transactions",
        transactions=transactions,
        start_date=start_date,
        end_date=end_date,
        accounts=account_options,
        total_spend=total_spend,
        total_income=total_income,
    )


@financial_bp.route("/analytics")
@login_required
def analytics():
    """Route for advanced interactive analytics."""
    try:
        # Get filter parameters from query string
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        categories = request.args.get("categories")
        accounts = request.args.get("accounts")

        # Set default values for date inputs if not provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # Process categories and accounts for display
        selected_categories = categories.split(",") if categories else []
        selected_accounts = accounts.split(",") if accounts else []

        # Get transactions for table with filters
        transactions = get_transactions_data(
            current_user.username,
            start_date=start_date,
            end_date=end_date,
            categories=categories,
            accounts=accounts,
        )

        # Get filtered data for charts
        filtered_monthly_data = get_monthly_data_with_filters(
            current_user.username,
            start_date=start_date,
            end_date=end_date,
            categories=categories,
            accounts=accounts,
        )

        filtered_category_data = get_category_data_with_filters(
            current_user.username,
            start_date=start_date,
            end_date=end_date,
            categories=categories,
            accounts=accounts,
        )

        # Generate chart HTML
        spending_chart_html = create_spending_chart_html(filtered_monthly_data)
        category_chart_html = create_category_chart_html(filtered_category_data)

        # Get all available category options for filter dropdown
        category_options = get_category_options(current_user.username)

        # Get all available account options for filter dropdown
        account_options = [
            {"id": b.plaid_account_id, "name": b.name}
            for b in Balance.query.filter_by(user_id=current_user.id).all()
        ]

        current_app.logger.info(
            f"Rendering analytics with filters: start={start_date}, end={end_date}, categories={categories}, accounts={accounts}"
        )
        current_app.logger.info(
            f"Found {len(transactions)} transactions matching filters"
        )

        return render_template(
            "financial/analytics.html",
            title="Financial Analytics",
            spending_chart_html=spending_chart_html,
            category_chart_html=category_chart_html,
            transactions=transactions,
            categories=category_options,
            accounts=account_options,
            start_date=start_date,
            end_date=end_date,
            selected_categories=selected_categories,
            selected_accounts=selected_accounts,
        )
    except Exception as e:
        current_app.logger.error(f"Analytics error: {str(e)}")
        flash(f"Error loading analytics: {str(e)}", "danger")

        # Return a simple page with error handling
        return render_template(
            "financial/analytics.html",
            title="Financial Analytics",
            spending_chart_html="<div class='text-center py-5'><p class='text-danger'>Error loading charts</p></div>",
            category_chart_html="<div class='text-center py-5'><p class='text-danger'>Error loading charts</p></div>",
            transactions=[],
            categories=[],
            accounts=[],
            start_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            end_date=datetime.now().strftime("%Y-%m-%d"),
            selected_categories=[],
            selected_accounts=[],
        )


# API Endpoints for AJAX requests
@financial_bp.route("/api/transactions")
@login_required
def api_transactions():
    """API endpoint for getting transactions as JSON."""
    # Default to last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    # Get date range from query params if provided
    if "start_date" in request.args and "end_date" in request.args:
        try:
            start_date = datetime.strptime(
                request.args.get("start_date"), "%Y-%m-%d"
            ).date()
            end_date = datetime.strptime(
                request.args.get("end_date"), "%Y-%m-%d"
            ).date()
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

    # Get filter by account if provided
    account_id = request.args.get("account_id")

    # Get transactions
    transactions = get_transactions(
        current_user.id, start_date, end_date, account_id=account_id
    )

    # Format for JSON response
    return jsonify(
        {
            "transactions": [t.to_dict() for t in transactions],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_count": len(transactions),
        }
    )


@financial_bp.route("/api/balances")
@login_required
def api_balances():
    """API endpoint for getting account balances as JSON."""
    balances = get_balances(current_user.id)
    return jsonify({"accounts": [b.to_dict() for b in balances]})


@financial_bp.route("/api/charts/trend")
@login_required
def monthly_trend_chart():
    """API endpoint for monthly spending trend chart data."""
    monthly_data = calculate_monthly_spending(current_user.username, with_details=True)
    return jsonify(create_monthly_trend_json(monthly_data))


@financial_bp.route("/api/charts/category")
@login_required
def category_breakdown_chart():
    """API endpoint for category breakdown chart data."""
    category_data = get_spending_by_category(current_user.username)
    return jsonify(category_data)


@financial_bp.route("/debug-charts")
@login_required
def debug_charts():
    """Debug route to test chart generation."""
    try:
        # Get basic chart data
        spending_categories = get_spending_by_category(current_user.username)
        current_app.logger.info(f"Spending categories: {spending_categories}")

        monthly_data = calculate_monthly_spending(
            current_user.username, with_details=True
        )
        current_app.logger.info(f"Monthly data: {monthly_data}")

        # Check for empty data
        if not spending_categories.get("labels"):
            current_app.logger.warning("No category data available")
            category_chart = json.dumps(
                {"data": [], "layout": {"title": "No data available"}}
            )
        else:
            # Create chart JSON
            category_chart = create_category_chart_html(spending_categories)

        if not monthly_data.get("labels"):
            current_app.logger.warning("No monthly data available")
            spending_chart = json.dumps(
                {"data": [], "layout": {"title": "No data available"}}
            )
        else:
            # Create chart JSON
            spending_chart = create_spending_chart_html(monthly_data)

        # Check if charts are generated
        current_app.logger.info(f"Category chart generated: {bool(category_chart)}")
        current_app.logger.info(f"Spending chart generated: {bool(spending_chart)}")

        # Create response with chart data for inspection
        response_data = {
            "user_id": current_user.id,
            "username": current_user.username,
            "categories_data": spending_categories,
            "monthly_data": monthly_data,
            "category_chart_available": bool(category_chart),
            "spending_chart_available": bool(spending_chart),
            "transaction_count": Transaction.query.filter_by(
                user_id=current_user.id
            ).count(),
        }

        return render_template(
            "financial/debug.html",
            title="Debug Charts",
            spending_chart=spending_chart,
            category_chart=category_chart,
            response_data=response_data,
        )
    except Exception as e:
        current_app.logger.error(f"Error in debug_charts: {str(e)}")
        flash(f"Error debugging charts: {str(e)}", "danger")
        return redirect(url_for("financial.dashboard"))


@financial_bp.route("/fix-data")
@login_required
def fix_data():
    """Route to fix issues with transaction data."""

    # Fix transaction data
    fix_transaction_data(username=current_user.username)

    # Debug transactions again to confirm fixes
    debug_transactions(username=current_user.username)

    flash("Transaction data has been fixed and verified.", "success")
    return redirect(url_for("financial.debug_charts"))
