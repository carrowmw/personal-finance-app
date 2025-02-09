# application/frontend/src/dashboard/layout.py

from dash import html, dcc, dash_table, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from flask_login import current_user

from application.data.processing import get_transactions_df


def create_empty_figure(message="No data available"):
    """Create an empty figure with a message"""
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
    )
    fig.update_layout(
        xaxis={"visible": False},
        yaxis={"visible": False},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def create_spending_overview(username):
    """Create an overview of spending trends"""
    df = get_transactions_df(username)
    if df is None:
        return None

    # Convert date to datetime if it's not already
    df["date"] = pd.to_datetime(df["date"])

    # Create monthly spending trend
    monthly_spending = df.groupby(df["date"].dt.strftime("%Y-%m"))["amount"].sum()

    fig = go.Figure()

    # Add bar chart for monthly spending
    fig.add_trace(
        go.Bar(
            x=monthly_spending.index, y=monthly_spending.values, name="Monthly Spending"
        )
    )

    # Add trend line
    fig.add_trace(
        go.Scatter(
            x=monthly_spending.index,
            y=monthly_spending.values.rolling(3).mean(),
            name="3-Month Average",
            line=dict(color="red"),
        )
    )

    fig.update_layout(
        title="Monthly Spending Overview",
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        hovermode="x unified",
    )

    return fig


def create_category_sunburst(username):
    """Create a sunburst chart of spending by category and subcategory"""
    df = get_transactions_df(username)
    if df is None:
        return None

    # Group by category and subcategory
    grouped = df.groupby(["category", "subcategory"])["amount"].sum().reset_index()

    fig = px.sunburst(
        grouped,
        path=["category", "subcategory"],
        values="amount",
        title="Spending Distribution",
    )

    fig.update_layout(width=600, height=600)

    return fig


def create_transactions_by_category_graph(username):
    """Create a bar chart of spending by category"""
    df = get_transactions_df(username)
    if df is None:
        return None

    # Group by category
    category_spending = (
        df.groupby("category")["amount"].sum().sort_values(ascending=True)
    )

    fig = go.Figure(
        go.Bar(x=category_spending.values, y=category_spending.index, orientation="h")
    )

    fig.update_layout(
        title="Spending by Category",
        xaxis_title="Amount ($)",
        yaxis_title="Category",
        height=400
        + (len(category_spending) * 20),  # Adjust height based on number of categories
    )

    return fig


def create_recent_transactions_table(username):
    """Create a table of recent transactions"""
    df = get_transactions_df(username)
    if df is None:
        return None

    # Sort by date and get recent transactions
    recent_df = df.sort_values("date", ascending=False).head(10)

    # Format amounts as currency
    recent_df["amount"] = recent_df["amount"].apply(lambda x: f"${x:,.2f}")

    return dash_table.DataTable(
        id="recent-transactions",
        columns=[
            {"name": "Date", "id": "date"},
            {"name": "Name", "id": "name"},
            {"name": "Amount", "id": "amount"},
            {"name": "Category", "id": "category"},
            {"name": "Subcategory", "id": "subcategory"},
        ],
        data=recent_df.to_dict("records"),
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left", "padding": "10px", "minWidth": "100px"},
        style_header={"backgroundColor": "rgb(230, 230, 230)", "fontWeight": "bold"},
    )


def create_navbar(username):
    """Create the navigation bar"""
    return dbc.NavbarSimple(
        children=[
            dbc.NavItem(html.A("Home", href="/", className="nav-link")),
            dbc.NavItem(html.A("About", href="/about", className="nav-link")),
            dbc.NavItem(html.A("Posts", href="/posts", className="nav-link")),
            dbc.NavItem(html.A("Account", href="/account", className="nav-link")),
            dbc.NavItem(html.A("Logout", href="/logout", className="nav-link")),
        ],
        brand="Flask Finance App",
        brand_href="/",
        color="dark",
        dark=True,
        className="bg-steel"
    )


def create_transaction_buttons():
    """Create the transaction control buttons"""
    print("Creating transaction buttons")  # Debug log
    return html.Div(
        className="content-section",
        children=[
            html.Button(
                "Connect Bank Account",
                id="link-button",
                className="btn btn-primary mb-3 me-2",
                n_clicks=0  # Initialize click counter
            ),
            html.Button(
                "Get Transactions",
                id="transactions-button",
                className="btn btn-secondary mb-3 me-2",
                disabled=True
            ),
            html.Button(
                "Get Balance",
                id="balance-button",
                className="btn btn-secondary mb-3",
                disabled=True
            ),
            html.Div(id="plaid-link-container")
        ]
    )


def create_layout(username):
    """Create the Dash layout"""
    return html.Div([
        # Store components for the Plaid data
        dcc.Store(id='transaction-data', storage_type='memory'),
        dcc.Store(id='balance-data', storage_type='memory'),
        
        # Navigation
        create_navbar(username),
        
        # Main container
        dbc.Container([
            # Transaction Buttons
            create_transaction_buttons(),
            
            # Date Range Selector
            dbc.Row([
                dbc.Col([
                    html.Label("Select Date Range"),
                    dcc.Dropdown(
                        id='date-range',
                        options=[
                            {'label': 'Last 30 Days', 'value': '30'},
                            {'label': 'Last 90 Days', 'value': '90'},
                            {'label': 'Last Year', 'value': '365'}
                        ],
                        value='30'
                    )
                ])
            ]),
            
            # Spending Graph
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id='spending-graph',
                        figure={}
                    )
                ])
            ]),
            
            # Recent Transactions Table
            dbc.Row([
                dbc.Col([
                    html.H2("Recent Transactions"),
                    dash_table.DataTable(
                        id='recent-transactions',
                        columns=[
                            {"name": "Date", "id": "date"},
                            {"name": "Name", "id": "name"},
                            {"name": "Amount", "id": "amount"}
                        ],
                        data=[]
                    )
                ])
            ])
        ], className="mt-4")
    ])

# Update callbacks to include username
@callback(
    Output("category-sunburst", "figure"), Input("spending-overview", "clickData")
)
def update_category_view(click_data):
    if not current_user.is_authenticated:
        return create_empty_figure("Please log in to view data")
    if click_data is None:
        return create_category_sunburst(current_user.username)
    return create_category_sunburst(current_user.username)
