# application/data/models.py
from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from application.frontend.src import (
    db,
    login_manager,
)  # import app for the app secret key


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default="default.png")
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship("Post", backref="author", lazy=True)

    # Generate a token for the user
    def get_reset_token(self, expires_sec=1800):
        print("Debug - Before Serializer:")
        print(f"Secret Key Type: {type(current_app.config['SECRET_KEY'])}")
        print(f"Secret Key Value: {current_app.config['SECRET_KEY']}")

        try:
            s = Serializer(
                secret_key=current_app.config["APP_SECRET_KEY"],
                salt="reset-password",  # typically a rondom string would go here
                signer_kwargs={"key_derivation": "hmac"},
            )

            token = s.dumps({"user_id": self.id})
            print("Generated Token: {token}")
            return token
        except Exception as e:
            print(f"Error in token generation: {str(e)}")
            raise

    @staticmethod  # This is a static method, it does not take self as an argument
    # Verify the token
    def verify_reset_token(token):
        print("Debug - Token Verification:")
        print(f"Received Token: {token}")

        try:
            s = Serializer(
                secret_key=current_app.config["APP_SECRET_KEY"],
                salt="reset-password",  # typically a rondom string would go here (needs to be same as above)
                signer_kwargs={"key_derivation": "hmac"},
            )
            user_id = s.loads(token, max_age=1800)["user_id"]
            print(f"Decoded user_id: {user_id}")
            return User.query.get(user_id)
        except Exception as e:
            print(f"Token verification error: {str(e)}")
            return None

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


# typically a rondom string would go here


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now())
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"
