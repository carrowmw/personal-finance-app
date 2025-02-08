# application/frontend/src/config.py

import os


class FrontendConfig:
    """
    Configuration for the frontend application.
    """

    # Front-end configuration
    SECRET_KEY = os.getenv("APP_SECRET_KEY")  # Google app secret key
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")  # Database URI

    # Mail configuration
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("GMAIL_USER")
    MAIL_PASSWORD = os.getenv("GMAIL_PASS")

    # Validate required environment variables
    @classmethod
    def validate(cls):
        """
        Validate that all required environment variables are set.
        """
        required_vars = [
            "APP_SECRET_KEY",
            "SQLALCHEMY_DATABASE_URI",
            "GMAIL_USER",
            "GMAIL_PASS",
        ]

        for var in required_vars:
            if not getattr(cls, var):
                raise ValueError(f"Missing required environment variable: {var}")
