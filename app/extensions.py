# app/extensions.py

"""
Centralizes all Flask extensions
"""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()
cors = CORS()

# Configure login
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
