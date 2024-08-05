# application/frontend/dash_app/__init__.py

import dash
from flask import Flask
from application.frontend.dash_app.layout import create_layout


def create_dash_app(flask_app: Flask):
    dash_app = dash.Dash(
        __name__,
        server=flask_app,
        url_base_pathname="/dash/",
        external_stylesheets=["/static/main.css"],
    )

    dash_app.layout = create_layout
    return dash_app
