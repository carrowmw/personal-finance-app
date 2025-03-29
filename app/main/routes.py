# app/main/routes.py

from flask import render_template, request
from app.models import Post
from app.main import main_bp


@main_bp.route("/")
@main_bp.route("/home")
def home():
    return render_template("main/home.html")


@main_bp.route("/about")
def about():
    return render_template("main/about.html", title="About")
