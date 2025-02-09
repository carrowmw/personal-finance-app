# application/backend/src/__init__.py

from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager

login_manager = LoginManager()


def create_backend_app():
    app = Flask(__name__)
    CORS(app)

    # Initialise Flask-login
    login_manager.init_app(app)

    # Import and register blueprints
    from application.backend.src.routes import backend
    app.register_blueprint(backend)

    return app


@login_manager.user_loader
def load_user(user_id):
    from application.data.models import User
    return User.query.get(int(user_id))