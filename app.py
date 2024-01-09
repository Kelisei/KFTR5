from flask import Flask, abort, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import re

import src.utils as utils
from datetime import datetime
import base64
from datetime import timedelta
from werkzeug.middleware.proxy_fix import ProxyFix
import os
from src.model import db, User, Post, Follows

email_pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"
app.config["SESSION_PERMANENT"] = False
app.secret_key = os.environ.get("SECRET_KEY")
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
app.permanent_session_lifetime = timedelta(weeks=1)
app.wsgi_app = ProxyFix(app.wsgi_app)

Session(app)
bcrypt = Bcrypt(app)
db.init_app(app)
migrate = Migrate(app, db)
CORS(app)


def user_exists(username: str) -> bool:
    """
    Returns if that id corresponds to a user stored
    in the database, if the id is null then returns false.
    """
    return bool(User.query.filter_by(username=username).first())


def is_logged() -> bool:
    return bool(session.get("id"))


def user_info(username: str):
    return User.query.filter_by(username=username).first()


def user_posts(user_id: int):
    return (
        db.session.query(Post, User)
        .join(User, Post.author_id == User.user_id)
        .filter(User.user_id == user_id)
        .all()
    )


def get_follow(followed_id: int, follower_id: int) -> Follows | None:
    return Follows.query.filter_by(
        followed_id=followed_id, follower_id=follower_id
    ).first()


@app.errorhandler(404)
def page_not_found(error):
    return render_template("page_not_found.html"), 404

@app.route("/like", methods=["POST"])
def like():
    


@app.route("/int:post_id>", methods=["GET"])
def see_post(post_id:int):
    if is_logged():
        post = Post.query.filter_by(post_id=post_id).first()
        if bool(post):
            replies = Post.query.filter_by(answered_post_id=post_id)
            replied = Post.query.filter_by(post_id=post.answered_post_id)
            return render_template("post.html", post=post, replies=replies, replied=replied)
    return redirect("/")

@app.route("/ownprofile", methods=["GET", "POST"])
def ownprofile():
    """Redirect to the profile of the currentyly logged user (with post
    request) or goes to login."""
    if is_logged():
        return redirect(
            url_for(
                "profile",
                username=User.query.filter_by(user_id=session.get("id"))
                .first()
                .username,
            )
        )
    return redirect("/login")


@app.route("/follow/<username>", methods=["POST"])
def follow(username: str):
    if is_logged():
        if user_exists(username):
            followed_id = user_info(username).user_id
            follow = get_follow(followed_id, session.get("id"))
            if not bool(follow):
                follow = Follows(
                    followed_id=followed_id,
                    follower_id=session.get("id"),
                    follow_date=datetime.now().date(),
                    follow_hour=datetime.now().time(),
                )
                db.session.add(follow)
            else:
                db.session.delete(follow)
            db.session.commit()
        return redirect(url_for("profile", username=username))
    redirect("/")


@app.route("/<username>/edit", methods=["POST"])
def edit_profile(username: str):
    if user_exists(username) and is_logged():
        profile_info = user_info(username)
        if session.get("id") == profile_info.user_id:
            new_username = request.form.get("username")
            if bool(new_username) or len(new_username) <= 30:
                username=new_username
                profile_info.username = new_username
            new_email = request.form.get("email")
            if bool(new_email) or email_pattern.match(new_email):
                profile_info.email = new_email
            new_bio = request.form.get("bio")
            if bool(new_bio) and len(new_bio) < 256:
                profile_info.bio = new_bio
            new_website = request.form.get("website")
            if bool(new_website) and len(new_website) < 256:
                profile_info.website = new_website
            pfp = request.files.get("pfp").read()
            if bool(pfp):
                pfp = base64.b64encode(utils.make_pfp(pfp, 300))
                profile_info.profile_picture = pfp
            print(profile_info)
            db.session.commit()
            return redirect(url_for("profile", username=username))
    return redirect("/")


@app.route("/<username>", methods=["GET"])
def profile(username):
    if not is_logged:
        return redirect("/login")
    profile_info = user_info(username)
    if not profile_info:
        abort(404)
    return render_template(
        "profile.html",
        user=profile_info,
        posts=user_posts(profile_info.user_id),
        ownprofile=session.get("id") == profile_info.user_id,
        followed=bool(
            Follows.query.filter_by(
                followed_id=profile_info.user_id, follower_id=session.get("id")
            ).first()
        ),
    )


@app.route("/", methods=["GET", "POST"])
def feed():
    if request.method == "GET" and session.get("id"):
        return render_template(
            "feed.html",
            posts=list(
                reversed(
                    db.session.query(Post, User)
                    .join(User, Post.author_id == User.user_id)
                    .all()
                )
            )[:100],
        )
    if request.method == "POST":
        session["id"] = None
    return redirect("/login")


@app.route("/new_post", methods=["POST"])
def new_post():
    text = request.form.get("text")
    image = request.files.get("image")
    image = image.read()
    if image:
        image = base64.b64encode(utils.optimize_image(image))
    else:
        image = None
    id = session.get("id")
    if id and text:
        user_post = Post(
            post_date=datetime.now().date(),
            post_hour=datetime.now().time(),
            author_id=id,
            text=text,
            image=image,
        )
        db.session.add(user_post)
        db.session.commit()
        return redirect("/")
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("id"):
        redirect("/")
    if request.method == "GET":
        return render_template("login.html", message="")
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            session["id"] = user.user_id
            return redirect("/")
        return render_template("login.html", message="Invalid email or password")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("id"):
        redirect("/")
    country_names = utils.get_country_names(lower=False)
    if request.method == "GET":
        print(User.query.all())
        return render_template("register.html", message="", countries=country_names)
    if request.method == "POST":
        user_data = {"username": request.form.get("username")}
        user_data["email"] = request.form.get("email")
        user_data["password"] = request.form.get("password")
        user_data["country"] = request.form.get("country")
        user_data["image"] = request.files.get("image")
        result = validate_user_info(user_data, country_names)
        if result[0]:
            return render_template(
                "register.html",
                message=result[1],
                countries=country_names,
            )
        process_registration(user_data)
        return redirect("/")


def process_registration(user_data: dict):
    """
    Processes the user registration data.

    Args:
        user_data (dict): A dictionary containing the user registration data.

    Returns:
        None
    """

    image_binary = base64.b64encode(utils.make_pfp(user_data["image"].read(), 300))
    password_hash = bcrypt.generate_password_hash(user_data["password"])
    new_user = User(
        username=user_data["username"],
        email=user_data["email"],
        password_hash=password_hash,
        profile_picture=image_binary,
        country=user_data["country"],
        approved=False,
        registration_date=datetime.now().date(),
        registration_hour=datetime.now().time(),
    )

    db.session.add(new_user)
    db.session.commit()


def validate_user_info(
    user_data: dict, country_names: list[str]
) -> tuple[bool, str]:
    """
    Validates the user registration data.

    Args:
        user_data (dict): A dictionary containing the user registration data.

    Returns:
        tuple(bool, str): A tuple indicating if the validation passed or not, and an error message if any validation fails.
    """

    if not user_data["username"] or len(user_data["username"]) > 30:
        return (True, "Pick a username with a length between 1 and 30 characters")
    if User.query.filter_by(username=user_data["username"]).first():
        return (True, "That username already exists")
    if not user_data["email"] or not email_pattern.match(user_data["email"]):
        return (True, "Please enter a valid email, i.e: example@gmail.com")
    if User.query.filter_by(email=user_data["email"]).first():
        return (True, "That email is already in use")
    if (
        len(user_data["password"]) < 7
        or len(user_data["password"]) > 30
        or not re.search(r"\d", user_data["password"])
    ):
        return (
            True,
            "Please enter a valid password (minimum 6 characters with a number)",
        )
    if user_data["country"] not in country_names:
        return (True, "Not a valid country")
    if not user_data["image"]:
        return (True, "Profile picture not loaded")
    if not utils.is_allowed_format(user_data["image"].filename):
        return (True, "Introduce a valid image (png, jpg, gif)")
    return (False, "")


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
