# application/frontend/dash_app/layout.py

from dash import html, dcc, dash_table, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px

from application.frontend.dash_app.munging import get_balance_df, get_transactions_df


def create_balance_graph():

    balance_df = get_balance_df()
    if balance_df is None:
        return None
    fig = px.bar(data_frame=balance_df, x="name", y="current", title="Current Balances")
    return fig


def create_transactions_by_category_data():
    transactions_df = get_transactions_df()
    if transactions_df is None:
        return None
    transactions_df = transactions_df[["category", "amount"]]
    if transactions_df is None:
        return None
    grouped_data = transactions_df.groupby("category").sum()
    return grouped_data


def create_transactions_by_subcategory_graph(category=None):
    transactions_df = get_transactions_df()
    if transactions_df is None or category is None:
        return px.bar(title="Click a category to see subcategories")

    filtered_df = transactions_df[transactions_df["category"] == category]
    grouped_data = filtered_df.groupby("subcategory")["amount"].sum().reset_index()

    fig = px.bar(
        grouped_data,
        x="subcategory",
        y="amount",
        title=f"Transactions by Subcategory for {category}",
    )
    return fig


def create_transactions_by_category_graph():
    data = create_transactions_by_category_data()
    if data is None:
        return None
    fig = px.bar(x=data.index, y=data["amount"], title="Transactions by Category")
    return fig


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
                        html.P(balance_df.to_dict("records")),
                        dash_table.DataTable(
                            id="balance-table",
                            data=balance_df.to_dict("records"),
                            columns=[{"name": i, "id": i} for i in balance_df.columns],
                            page_size=4,
                        ),
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
                        html.H4(
                            "No transactions data available", className="card-title"
                        ),
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
                        html.Div(
                            dash_table.DataTable(
                                id="transactions-table",
                                data=transactions.to_dict("records"),
                                columns=[
                                    {"name": i, "id": i} for i in transactions.columns
                                ][:8],
                                page_size=8,
                            ),
                        ),
                    ]
                )
            ]
        )


def create_layout():
    # Example of a simple Plotly Dash layout

    return html.Div(
        children=[
            html.Div(
                children=[
                    get_balance_card(),
                ]
            ),
            html.Div(
                children=[
                    dcc.Graph(id="balance-graph", figure=create_balance_graph()),
                ]
            ),
            html.Div(
                children=[
                    get_transactions_card(),
                ]
            ),
            html.Div(
                children=[
                    dcc.Graph(
                        id="transactions-by-category-graph",
                        figure=create_transactions_by_category_graph(),
                    ),
                ]
            ),
            html.Div(
                children=[
                    dcc.Graph(
                        id="transactions-by-subcategory-graph",
                        figure=create_transactions_by_subcategory_graph(),
                    ),
                ]
            ),
        ]
    )


@callback(
    Output("transactions-by-subcategory-graph", "figure"),
    Input("transactions-by-category-graph", "clickData"),
)
def update_subcategory_graph(clickData):
    if clickData is None:
        return create_transactions_by_subcategory_graph()

    category = clickData["points"][0]["x"]
    return create_transactions_by_subcategory_graph(category)
