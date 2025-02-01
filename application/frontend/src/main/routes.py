# application/frontend/src/main/routes.py

from flask import Blueprint, render_template, request
from application.data.models import Post

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    return render_template("home.html")


@main.route("/posts")
def posts():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=2)
    return render_template("posts.html", posts=posts)


@main.route("/about")
def about():
    return render_template("about.html", title="About")