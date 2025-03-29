# app/financial/__init__.py

from flask import Blueprint

financial_bp = Blueprint(
    "financial", __name__, url_prefix="/financial", template_folder="templates"
)

from app.financial import routes
