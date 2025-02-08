# application/frontend/src/dashboard/routes.py

from flask import Blueprint, render_template
from flask_login import login_required

# from application.data.models import Transactions
from application.frontend.src import db

dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/dashboard", methods=["GET", "POST"])
@login_required
def transactions(username):
    # transactions = Transactions.query.all()
    return render_template("transactions.html")  # , transactions=transactions)
