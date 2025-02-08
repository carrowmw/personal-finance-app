import os


class BackendConfig:
    """
    Configuration for the backend application.
    """

    # Plaid configuration
    ALLOWED_ORIGINS = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:5010,http://192.0.0.2:5010"
    ).split(",")
    PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
    PLAID_SECRET_KEY = os.getenv("PLAID_SECRET_KEY")
    PLAID_ENV = os.getenv("PLAID_ENV")
    PLAID_USER_ID = os.getenv("PLAID_USER_ID")
    PLAID_PRODUCTS = os.getenv("PLAID_PRODUCTS")
    PLAID_COUNTRY_CODES = os.getenv("PLAID_COUNTRY_CODES")
    PLAID_REDIRECT_URI = os.getenv("PLAID_REDIRECT_URI", "http://localhost:5010")

    # Validate required environment variables
    @classmethod
    def validate(cls):
        """
        Validate that all required environment variables are set.
        """
        required_vars = [
            "PLAID_CLIENT_ID",
            "PLAID_SECRET_KEY",
            "PLAID_ENV",
            "PLAID_USER_ID",
            "PLAID_PRODUCTS",
            "PLAID_COUNTRY_CODES",
            "PLAID_REDIRECT_URI",
        ]

        for var in required_vars:
            if not getattr(cls, var):
                raise ValueError(f"Missing required environment variable: {var}")
