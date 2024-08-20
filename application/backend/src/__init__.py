# application/backend/src/__init__.py

from flask import Flask
from flask_cors import CORS


def create_backend_app():
    app = Flask(__name__)
    CORS(app)

    # Import routes
    from application.backend.src.routes import backend

    # Register blueprints
    app.register_blueprint(backend)

    return app
