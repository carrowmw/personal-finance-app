from flask import render_template, url_for, flash, redirect, request, abort
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Post
from app.posts.forms import PostForm
from app.posts import posts_bp


@posts_bp.route("/")
def index():
    """Route for viewing all posts."""
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template("posts/posts.html", posts=posts)


@posts_bp.route("/post/new", methods=["GET", "POST"])
@login_required
def new_post():
    """Route for creating a new post."""
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data, content=form.content.data, author=current_user
        )
        db.session.add(post)
        db.session.commit()
        flash("Your post has been created!", "success")
        return redirect(url_for("main.home"))
    return render_template(
        "posts/create_post.html", title="New Post", form=form, legend="New Post"
    )


@posts_bp.route("/post/<int:post_id>")
def post(post_id):
    """Route for viewing a specific post."""
    post = Post.query.get_or_404(post_id)
    return render_template("posts/post.html", title=post.title, post=post)


@posts_bp.route("/post/<int:post_id>/update", methods=["GET", "POST"])
@login_required
def update_post(post_id):
    """Route for updating a post."""
    post = Post.query.get_or_404(post_id)
    # Check if the current user is the author of the post
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash("Your post has been updated!", "success")
        return redirect(url_for("posts.post", post_id=post.id))
    elif request.method == "GET":
        # Pre-populate the form with existing data
        form.title.data = post.title
        form.content.data = post.content
    return render_template(
        "posts/create_post.html", title="Update Post", form=form, legend="Update Post"
    )


@posts_bp.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    """Route for deleting a post."""
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Your post has been deleted!", "success")
    return redirect(url_for("main.home"))


@posts_bp.route("/user/<string:username>/posts")
def user_posts(username):
    """Route for viewing all posts by a specific user."""
    from app.models import User

    page = request.args.get("page", 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = (
        Post.query.filter_by(author=user)
        .order_by(Post.date_posted.desc())
        .paginate(page=page, per_page=5)
    )
    return render_template("posts/user_posts.html", posts=posts, user=user)
