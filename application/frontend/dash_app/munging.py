import pandas as pd
from application.backend.src.utils import load_balance, load_transactions


# Function to split the category list into separate columns
def split_category(category_list):
    if category_list is None:
        return pd.Series([None, None])
    elif len(category_list) >= 2:
        return pd.Series([category_list[0], category_list[1]])
    elif len(category_list) == 1:
        return pd.Series([category_list[0], None])
    else:
        return pd.Series([None, None])


def get_transactions_df():
    if not load_transactions():
        return None
    transactions = load_transactions()
    transactions_df = pd.DataFrame(transactions)
    subset_of_columns = [
        "account_id",
        "amount",
        "category",
        "date",
        "iso_currency_code",
        "merchant_name",
        "name",
    ]
    transactions_df = transactions_df[subset_of_columns]
    # Apply the function to the 'category' column
    category_df = transactions_df["category"].apply(split_category)
    # Rename the new columns
    category_df.columns = ["category", "subcategory"]
    # Concatenate the new columns with the original DataFrame
    expanded_transactions_df = pd.concat(
        [transactions_df.drop(columns=["category"]), category_df], axis=1
    )

    return expanded_transactions_df


def get_balance_df():
    if not load_balance():
        return None
    balance_data = load_balance()
    balance_df = pd.DataFrame(balance_data["accounts"])
    # Normalize the 'balances' column
    balances_df = pd.json_normalize(balance_df["balances"])
    # Concatenate the original DataFrame with the normalized 'balances' DataFrame
    expanded_balance_df = pd.concat(
        [balance_df.drop(columns=["balances"]), balances_df], axis=1
    )
    return expanded_balance_df
