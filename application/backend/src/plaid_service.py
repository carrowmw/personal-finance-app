# application/backend/src/plaid_service.py

import plaid
from plaid.api import plaid_api
from plaid.configuration import Environment
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from application.backend.src.utils import get_env_variables


def initialize_plaid_client():
    env_vars = get_env_variables()
    client_id = env_vars["PLAID_CLIENT_ID"]
    secret = env_vars["PLAID_SECRET"]
    environment = env_vars["PLAID_ENV"]

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
    try:
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = client.item_public_token_exchange(request)
        return response["access_token"]

    except plaid.exceptions.ApiException as e:
        print(f"Exception when calling PlaidApi: {e}")
        return None


# def get_balance(client: object, access_token):
#     try:
#         request = AccountsBalanceGetRequest(access_token=access_token)
#         response = client.accounts_balance_get(request)
#         return response["accounts"]

#     except plaid.exceptions.ApiException as e:
#         print(f"Exception when calling PlaidApi: {e}")
#         return None
