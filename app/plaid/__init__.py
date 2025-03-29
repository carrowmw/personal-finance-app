# app/plaid/__init__.py

from flask import Blueprint

plaid_bp = Blueprint("plaid", __name__)

from app.plaid import routes
