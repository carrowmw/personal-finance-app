# application/frontend/dash_app/layout.py
import pandas as pd

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px

from application.backend.src.utils import load_balance, load_transactions

def get_transactions_df():
    if not load_transactions():
        return None
    transactions = load_transactions()
    transactions_df = pd.DataFrame(transactions)
    return transactions_df

def get_balance_df():
    if not load_balance():
        return None
    balance_data = load_balance()
    balance_df = pd.DataFrame(balance_data['accounts'])
    return balance_df


def create_balance_graph():

    balance_df = get_balance_df()
    if balance_df is None:
        return None
    name = balance_df['name']
    current_balance = balance_df['balances'].apply(lambda x: x['current'])


    if balance_df is None:
        return None
    fig = px.bar(x=name, y=current_balance, title='Current Balances')
    return fig

def create_transactions_by_category_graph():
    transactions_df = get_transactions_df()
    if transactions_df is None:
        return None


def get_balance_card():
    balance_df = get_balance_df()
    if balance_df is None:
        return dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H4("No balance data available", className="card-title"),
                        html.P("Please link an account to view balance data."),
                    ]
                )
            ]
        )
    else:
        return dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H4("Balance Data", className="card-title"),
                        html.P("Balance data for linked accounts."),
                        dbc.Table.from_dataframe(balance_df, striped=True, bordered=True, hover=True),
                    ]
                )
            ]
        )

def get_transactions_card():
    transactions = get_transactions_df()
    if transactions is None:
        return dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H4("No transactions data available", className="card-title"),
                        html.P("Please link an account to view transactions data."),
                    ]
                )
            ]
        )
    else:
        return dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H4("Transactions Data", className="card-title"),
                        html.P("Transactions data for linked accounts."),
                        dbc.Table.from_dataframe(transactions, striped=True, bordered=True, hover=True),
                    ]
                )
            ]
        )

def create_layout():
    # Example of a simple Plotly Dash layout



    fig = px.line(x=[1, 2, 3], y=[4, 1, 2], title="Sample Plot")

    return html.Div(children=[
        html.Div(
        children=[
            html.H1(children="Plotly Dash Integration"),
            dcc.Graph(id="example-graph", figure=fig),
        ]
        ),
        html.Div(
            children=[
                get_balance_card(),
            ]
        ),
        html.Div(
            children=[
                dcc.Graph(id="balance-graph", figure=create_balance_graph()),
            ]
        )
    ]
    )



