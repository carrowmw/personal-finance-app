# app/__init__.py

"""
Sets up the application factory.
"""

from flask import Flask, render_template
from app.config import config
from app.extensions import db, bcrypt, login_manager, mail, cors
import os
import logging


def create_app(config_name=None):
    """Application factory."""
    if config_name is None:
        config_name = os.environ.get("FLASK_CONFIG", "default")

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])

    # Configure logging
    if not app.debug:
        # Set up file logging
        handler = logging.FileHandler("app.log")
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
    else:
        # Ensure all log messages show in the console during development
        app.logger.setLevel(logging.DEBUG)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    cors.init_app(app)

    # Register blueprints
    from app.auth import auth_bp
    from app.main import main_bp
    from app.plaid import plaid_bp
    from app.posts import posts_bp
    from app.financial import financial_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(plaid_bp, url_prefix="/plaid")
    app.register_blueprint(posts_bp, url_prefix="/posts")
    app.register_blueprint(financial_bp)

    # Register error handlers
    register_error_handlers(app)

    # Create database tables if needed
    with app.app_context():
        db.create_all()

    return app


def register_error_handlers(app):
    """Register error handlers."""

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    return app
