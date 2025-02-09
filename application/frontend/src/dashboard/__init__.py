# application/frontend/src/dashboard/__init__.py

import dash
from flask import Flask, request
from flask_login import current_user, login_required
import dash_bootstrap_components as dbc


def create_dash_app(flask_app: Flask):
    dash_app = dash.Dash(
        __name__,
        server=flask_app,
        url_base_pathname="/dashboard/", # This specifies the endpoint name used in the routes.
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            "/static/main.css"
        ],
        external_scripts=[
            # Add Plaid script
            "https://cdn.plaid.com/link/v2/stable/link-initialize.js",
        ],
        serve_locally=False
    )

    # Import layout creation after Dash init
    from application.frontend.src.dashboard.layout import create_layout

    def serve_layout():
        if not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
            return dbc.Container([
                dbc.Alert("Please log in to view the dashboard", color="warning")
            ])
        return create_layout(current_user.username)

    dash_app.layout = serve_layout

    # Protect all Dash views with Flask-Login
    for view_function in dash_app.server.view_functions:
        if view_function.startswith(dash_app.config.url_base_pathname):
            dash_app.server.view_functions[view_function] = login_required(
                dash_app.server.view_functions[view_function]
            )

    # Register callbacks
    from application.frontend.src.dashboard import callbacks, clientside

    return dash_app
