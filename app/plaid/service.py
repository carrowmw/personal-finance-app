# app/plaid/service.py

import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from datetime import datetime, timedelta
from flask import current_app
import os


def initialize_plaid_client():
    """Initialize the Plaid client."""
    client_id = current_app.config.get("PLAID_CLIENT_ID")
    secret = current_app.config.get("PLAID_SECRET_KEY")
    environment = current_app.config.get("PLAID_ENV", "sandbox")

    if not client_id or not secret:
        current_app.logger.error("Plaid credentials not configured")
        return None

    environment_mapping = {
        "sandbox": plaid.Environment.Sandbox,
        "production": plaid.Environment.Production,
    }

    plaid_env = environment_mapping.get(environment, plaid.Environment.Sandbox)

    configuration = plaid.Configuration(
        host=plaid_env,
        api_key={
            "clientId": client_id,
            "secret": secret,
        },
    )

    api_client = plaid.ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)


def create_link_token(user_id):
    """Create a link token for the user."""
    client = initialize_plaid_client()
    if not client:
        return None

    # Get configuration from app config
    products_str = current_app.config.get("PLAID_PRODUCTS")
    products_list = [p.strip() for p in products_str.split(",")]
    country_codes_str = current_app.config.get("PLAID_COUNTRY_CODES")
    country_codes_list = [c.strip() for c in country_codes_str.split(",")]
    redirect_uri = current_app.config.get("PLAID_REDIRECT_URI")

    # Log the configuration
    current_app.logger.info(f"Using redirect URI: {redirect_uri}")
    current_app.logger.info(f"Products: {products_list}")
    current_app.logger.info(f"Country codes: {country_codes_list}")

    # Convert strings to enum values
    products = [Products(p) for p in products_list if p]
    country_codes = [CountryCode(c) for c in country_codes_list if c]

    # Create request including webhook if configured
    webhook_url = current_app.config.get("PLAID_WEBHOOK")
    request_params = {
        "user": LinkTokenCreateRequestUser(client_user_id=str(user_id)),
        "client_name": "Personal Finance App",
        "products": products,
        "country_codes": country_codes,
        "language": "en",
    }

    # Only add webhook if it's configured
    if webhook_url and isinstance(webhook_url, str):
        request_params["webhook"] = webhook_url

    # Only add redirect_uri if it's configured
    if redirect_uri and isinstance(redirect_uri, str):
        request_params["redirect_uri"] = redirect_uri

    try:
        request = LinkTokenCreateRequest(**request_params)
        response = client.link_token_create(request)
        return response["link_token"]
    except plaid.ApiException as e:
        current_app.logger.error(f"Error creating link token: {e}")
        return None


def exchange_public_token(public_token):
    """Exchange a public token for an access token."""
    client = initialize_plaid_client()
    if not client or not public_token:
        return None

    try:
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = client.item_public_token_exchange(request)
        return response["access_token"]
    except plaid.ApiException as e:
        current_app.logger.error(f"Error exchanging public token: {e}")
        return None


def get_accounts(access_token):
    """Get accounts for a user using their access token."""
    client = initialize_plaid_client()
    if not client or not access_token:
        return None

    try:
        request = AccountsGetRequest(access_token=access_token)
        response = client.accounts_get(request)
        return response["accounts"]
    except plaid.ApiException as e:
        current_app.logger.error(f"Error getting accounts: {e}")
        return None
