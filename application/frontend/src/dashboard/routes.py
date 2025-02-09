# application/frontend/src/dashboard/routes.py

from flask import Blueprint, redirect, url_for
from flask_login import login_required, current_user

from application.frontend.src import db

dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/dashboard", methods=["GET", "POST"])
@login_required
def transactions():
    # Redirect to the Dash app directly (rendering templates leads to nested pages)
    return redirect("/dashboard/")