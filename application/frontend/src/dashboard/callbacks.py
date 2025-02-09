from dash import Input, Output, callback, State
import plotly.graph_objects as go
from flask_login import current_user
from application.data.processing import get_transactions_df
from dash.exceptions import PreventUpdate
import pandas as pd

@callback(
    Output('spending-graph', 'figure'),
    [Input('transaction-store', 'data'),
     Input('date-range', 'value')]
)
def update_spending_graph(transactions_data, date_range):
    """Update the spending graph based on selected date range"""
    if not transactions_data:
        return create_empty_figure("No transaction data available")
    
    # Convert store data back to dataframe
    df = pd.DataFrame(transactions_data)
    
    try:
        if not current_user.is_authenticated:
            return create_empty_figure("Please log in to view data")
            
        if df is None or df.empty:
            return create_empty_figure("No transaction data available")

        # Create and return the figure
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=df['date'],
                y=df['amount'],
                name='Spending'
            )
        )
        
        fig.update_layout(
            title="Spending Overview",
            xaxis_title="Date",
            yaxis_title="Amount ($)",
            template="plotly_white"
        )
        
        return fig
        
    except Exception as e:
        print(f"Error in callback: {str(e)}")  # For debugging
        return create_empty_figure("Error loading data")

def create_empty_figure(message="No data available"):
    """Create an empty figure with a message"""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False
    )
    fig.update_layout(
        xaxis={"visible": False},
        yaxis={"visible": False},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

# Callback to update transaction store and table
@callback(
    [Output('transaction-store', 'data'),
     Output('recent-transactions', 'data')],
    Input('transactions-button', 'n_clicks'),
    prevent_initial_call=True
)
def update_transactions(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    
    df = get_transactions_df(current_user.username)
    if df is None or df.empty:
        return None, []
    
    # Format the data for the table
    recent_df = df.sort_values("date", ascending=False).head(10)
    recent_df["amount"] = recent_df["amount"].apply(lambda x: f"${x:,.2f}")
    
    return df.to_dict('records'), recent_df.to_dict('records')

# Callback to update balance store
@callback(
    Output('balance-store', 'data'),
    Input('balance-button', 'n_clicks'),
    prevent_initial_call=True
)
def update_balance(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    
    # Get balance data from your backend
    # This will be triggered by the balance button click
    return {'balance': 0}  # Replace with actual balance data

@callback(
    [Output('transactions-button', 'disabled'),
     Output('balance-button', 'disabled')],
    Input('access-token-store', 'data')
)
def update_button_states(access_token):
    """Enable/disable buttons based on access token availability"""
    disabled = access_token is None
    return disabled, disabled

@callback(
    Output('transaction-store', 'data'),
    Input('transactions-button', 'n_clicks'),
    State('access-token-store', 'data'),
    prevent_initial_call=True
)
def get_transactions(n_clicks, access_token):
    """Fetch transactions when button is clicked"""
    if not access_token:
        raise PreventUpdate
    
    return get_transactions_df(current_user.username).to_dict('records')

# Add more callbacks as needed