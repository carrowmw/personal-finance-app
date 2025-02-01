# application/frontend/src/__init__.py

# pylint: disable=unused-import
# pylint: disable=import-outside-toplevel

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv
from application.frontend.src.config import Config

# Load environment variables so os.environ.get() can access them
load_dotenv()

# Initialize extensions
db = SQLAlchemy()  # Initialize database
bcrypt = Bcrypt()  # Initialize bcrypt
login_manager = LoginManager()  # Initialize login manager
login_manager.login_view = "users.login"  # Redirect to login page if user tries to access login_required route
login_manager.login_message_category = "info"  # Bootstrap class for flash message
mail = Mail()  # Initialize mail


def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)  # Initialize database with app
    bcrypt.init_app(app)  # Initialize bcrypt with app
    login_manager.init_app(app)  # Initialize login manager with app
    mail.init_app(app)  # Initialize mail with app

    # After setting SECRET_KEY
    print(f"DEBUG: Mail Username: {app.config['MAIL_USERNAME']}")
    print(f"DEBUG: Mail Password is set: {'Yes' if app.config['MAIL_PASSWORD'] else 'No'}")
    print(f"DEBUG: Mail Password: {app.config["MAIL_PASSWORD"]}")
    print(f"DEBUG: Secret Key Type: {type(app.config['SECRET_KEY'])}")
    print(f"DEBUG: Secret Key Value: {app.config['SECRET_KEY']}")
    print(f"DEBUG: Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    with app.app_context():
        from application.data.models import (
            User,
            Post,
        )  # Import models to avoid circular imports

        db.create_all()  # Create database tables

        # Import frontend routes
        from application.frontend.src.users.routes import users  # Import user routes
        from application.frontend.src.posts.routes import posts  # Import user routes
        from application.frontend.src.main.routes import main  # Import user routes
        from application.frontend.src.errors.handlers import errors

        app.register_blueprint(users)  # Register frontend routes
        app.register_blueprint(posts)
        app.register_blueprint(main)
        app.register_blueprint(errors)

        from application.frontend.dash_app import create_dash_app  # Import Dash app

        create_dash_app(app)  # Create Dash app

    return app  # Return app instance
