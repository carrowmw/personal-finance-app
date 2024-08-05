# application/frontend/app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from application.frontend.app.routes import main
from application.frontend.dash_app import create_dash_app

app = Flask(__name__)
# Configuration
app.config["SECRET_KEY"] = "5b71ce8606eaf1aebb79156fc9fbe1bf"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
# Register blueprints
app.register_blueprint(main)
# Initialize the Dash app
create_dash_app(app)
