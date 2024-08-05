# application/frontend/app/routes.py

from flask import Blueprint, render_template, url_for, flash, redirect
from application.frontend.app.forms import RegistrationForm, LoginForm

main = Blueprint("main", __name__)

# Example data
posts = [
    {
        "author": "Carrow Morris-Wiltshire",
        "title": "Blog Post 1",
        "content": "First post content",
        "date_posted": "August 1st, 2024",
    },
    {
        "author": "Carrow Morris-Wiltshire",
        "title": "Blog Post 2",
        "content": "Second post content",
        "date_posted": "August 2nd, 2024",
    },
]


@main.route("/")
@main.route("/home")
def home():
    return render_template("home.html", posts=posts)


@main.route("/about")
def about():
    return render_template("about.html", title="About")


@main.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f"Account created for {form.username.data}!", "success")
        return redirect(url_for("main.home"))
    return render_template("register.html", title="Register", form=form)


@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.email.data == "admin@blog.com" and form.password.data == "password":
            flash("You have been logged in!", "success")
            return redirect(url_for("main.home"))
        else:
            flash("Login Unsuccessful. Please check username and password.", "danger")
    return render_template("login.html", title="Login", form=form)
