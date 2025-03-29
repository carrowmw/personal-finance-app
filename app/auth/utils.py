# application/frontend/src/users/utils.py

import os
import secrets
from PIL import Image
from flask import current_app, url_for
from flask_mail import Message
from app.extensions import mail


def save_picture(form_picture):
    """Save profile picture with a random name and resize it."""
    # Generate random filename to avoid collisions
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_filename = random_hex + f_ext

    # Create path and ensure directory exists
    picture_path = os.path.join(
        current_app.root_path, "static/profile_pics", picture_filename
    )
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)

    # Resize image to save space and improve load times
    output_size = (125, 125)
    image = Image.open(form_picture)
    image.thumbnail(output_size)
    image.save(picture_path)

    return picture_filename


def send_reset_email(user):
    """Send a password reset email to the user."""
    token = user.get_reset_token()
    msg = Message(
        "Password Reset Request",
        sender="noreply@personalfinance.app",
        recipients=[user.email],
    )
    msg.body = f"""To reset your password, visit the following link:
{url_for('auth.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
"""
    mail.send(msg)
