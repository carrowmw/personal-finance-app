# application/backend/src/utils.py

import os
import json
import pickle

ENV_PATH = "./application/backend/.env"
ACCESS_TOKEN_FILE = "./application/backend/access_token.json"
CURSOR_FILE = "./application/backend/cursor.json"
TRANSACTIONS_FILE = "./application/data/transactions.pkl"
BALANCE_FILE = "./application/data/balance.pkl"


def pretty_print_response(response):
    print(json.dumps(response, indent=2, sort_keys=True, default=str))


def save_transactions(transactions):
    if not os.path.exists("./application/data"):
        os.makedirs("./application/data")
    with open(TRANSACTIONS_FILE, "wb") as f:
        print(f)
        print(type(f))
        pickle.dump(transactions, f)


def load_transactions():
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, "rb") as f:
            return pickle.load(f)
    return print("No transactions found")


def save_balance(balance):
    if not os.path.exists("./application/data"):
        os.makedirs("./application/data")
    with open(BALANCE_FILE, "wb") as f:
        pickle.dump(balance, f)


def load_balance():
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "rb") as f:
            return pickle.load(f)
    return print("No balance found")


def save_cursor(cursor):
    with open(CURSOR_FILE, "w", encoding="utf8") as f:
        json.dump({"cursor": cursor}, f)


def load_cursor():
    if os.path.exists(CURSOR_FILE):
        with open(CURSOR_FILE, "r", encoding="utf8") as f:
            data = json.load(f)
            return data.get("cursor", "")
    return ""


def get_env_variables():
    env_vars = {}
    with open(ENV_PATH, encoding="utf8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            key, value = line.strip().split("=")
            env_vars[key] = value
    return env_vars


def save_access_token(access_token):
    with open(ACCESS_TOKEN_FILE, "w", encoding="utf8") as f:
        json.dump({"access_token": access_token}, f)


def load_access_token():
    if os.path.exists(ACCESS_TOKEN_FILE):
        with open(ACCESS_TOKEN_FILE, "r", encoding="utf8") as f:
            data = json.load(f)
            return data.get("access_token")
    return None


def format_error(e):
    response = json.loads(e.body)
    return {
        "error": {
            "status_code": e.status,
            "display_message": response["error_message"],
            "error_code": response["error_code"],
            "error_type": response["error_type"],
        }
    }
