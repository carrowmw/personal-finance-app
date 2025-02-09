# application/frontend/src/__init__.py

# pylint: disable=unused-import
# pylint: disable=import-outside-toplevel

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv
from application.frontend.src.config import FrontendConfig as Config

# Load environment variables so os.environ.get() can access them
load_dotenv()

# Initialize extensions
db = SQLAlchemy()  # Initialize database
bcrypt = Bcrypt()  # Initialize bcrypt
login_manager = LoginManager()  # Initialize login manager
login_manager.login_view = (
    "users.login"  # Redirect to login page if user tries to access login_required route
)
login_manager.login_message_category = "info"  # Bootstrap class for flash message
mail = Mail()  # Initialize mail


def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)  # Initialize database with app
    bcrypt.init_app(app)  # Initialize bcrypt with app
    login_manager.init_app(app)  # Initialize login manager with app
    mail.init_app(app)  # Initialize mail with app

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        # Import frontend routes
        from application.frontend.src.main.routes import main  # Import main routes
        from application.frontend.src.dashboard.routes import dashboard  # Import dashboard routes
        from application.frontend.src.users.routes import users  # Import user routes
        from application.frontend.src.posts.routes import posts  # Import post routes
        from application.frontend.src.errors.handlers import errors
        # Register frontend routes
        app.register_blueprint(main)
        app.register_blueprint(dashboard)
        app.register_blueprint(users)
        app.register_blueprint(posts)
        app.register_blueprint(errors)
        # Import models to avoid circular imports
        from application.data.models import (
            User,
            Post,
            Transaction,
            Balance,
        )  
        db.create_all()  # Create database tables
        # Initialize Dash app last
        from application.frontend.src.dashboard import create_dash_app
        create_dash_app(app)

    return app  # Return app instance
