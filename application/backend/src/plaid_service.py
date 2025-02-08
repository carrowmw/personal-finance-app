# application/backend/src/plaid_service.py

import plaid
from plaid.api import plaid_api
from plaid.configuration import Environment
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from application.backend.src.config import BackendConfig as Config


def initialize_plaid_client():
    """
    Initialize the Plaid client.
    :return: Plaid client object
    """
    Config.validate()
    client_id = Config.PLAID_CLIENT_ID
    secret = Config.PLAID_SECRET_KEY
    environment = Config.PLAID_ENV

    environment_mapping = {
        "sandbox": Environment.Sandbox,
        "production": Environment.Production,
    }

    if environment == "production":
        print("WARNING: Plaid client is in production mode")

    configuration = plaid.configuration.Configuration(
        host=environment_mapping[environment],
        api_key={"clientId": client_id, "secret": secret},
    )

    api_client = plaid_api.ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)


def create_link_token(client: object, user_id, country_codes, products):
    """
    Create a link token for the user.
    :param client: Plaid client object
    :param user_id: User ID
    :param country_codes: Country codes
    :param products: Products
    :return: Link token
    """
    try:
        request = LinkTokenCreateRequest(
            user={"client_user_id": user_id},
            products=[Products(products)],
            client_name="Personal Finance App",
            country_codes=[CountryCode(country_codes)],
            language="en",
        )
        response = client.link_token_create(request)
        return response["link_token"]

    except plaid.exceptions.ApiException as e:
        print(f"Exception when calling PlaidApi: {e}")
        return None


def exchange_public_token(client: object, public_token):
    """
    Exchange a public token for an access token.
    :param client: Plaid client object
    :param public_token: Public token
    :return: Access token
    """
    try:
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = client.item_public_token_exchange(request)
        return response["access_token"]

    except plaid.exceptions.ApiException as e:
        print(f"Exception when calling PlaidApi: {e}")
        return None
