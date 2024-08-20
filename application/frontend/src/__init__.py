# application/frontend/src/__init__.py


# pylint: disable=unused-import
# pylint: disable=import-outside-toplevel

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

db = SQLAlchemy()  # Initialize database
bcrypt = Bcrypt()  # Initialize bcrypt
login_manager = LoginManager()  # Initialize login manager


def create_app():
    app = Flask(__name__)
    # Configuration
    app.config["SECRET_KEY"] = "5b71ce8606eaf1aebb79156fc9fbe1bf"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"

    db.init_app(app)  # Initialize database
    bcrypt.init_app(app)  # Initialize bcrypt
    login_manager.init_app(app)  # Initialize login manager
    login_manager.login_view = "frontend.login"  # Redirect to login page if user tries to access login_required route
    login_manager.login_message_category = "info"  # Bootstrap class for flash message

    with app.app_context():
        from application.data.models import (
            User,
            Post,
        )  # Import models to avoid circular imports

        db.create_all()  # Create database tables

        # Import frontend routes
        from application.frontend.src.routes import frontend  # Import frontend routes

        app.register_blueprint(frontend)  # Register frontend routes

        from application.frontend.dash_app import create_dash_app  # Import Dash app

        create_dash_app(app)  # Create Dash app

    return app  # Return app instance
