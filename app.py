from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
import re
import utils
from datetime import datetime
import base64
from datetime import timedelta

email_pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"
app.config["SESSION_PERMANENT"] = False
app.secret_key = "KeliseiVenturaPerronsio1GokuVegetta777"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
app.permanent_session_lifetime = timedelta(weeks=1)

Session(app)
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    bio = db.Column(db.Text)
    website = db.Column(db.String(255))
    profile_picture = db.Column(db.LargeBinary)
    registration_date = db.Column(db.Date)
    registration_hour = db.Column(db.Time)
    country = db.Column(db.String(50))
    approved = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username}, email={self.email}, bio={self.bio}, website={self.website}, country={self.country}, approved={self.approved}, {self.registration_date=} , {self.registration_hour=})>"


class Follows(db.Model):
    follow_id = db.Column(db.Integer, primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    follower_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    follow_date = db.Column(db.Date)
    follow_hour = db.Column(db.Time)


class Post(db.Model):
    post_id = db.Column(db.Integer, primary_key=True)
    post_date = db.Column(db.Date)
    post_hour = db.Column(db.Time)
    author_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    text = db.Column(db.Text)
    image = db.Column(db.LargeBinary)

    def __repr__(self):
        return f"<Post({self.post_id=},{self.text=},{self.post_hour=},{self.post_date=},{self.author_id=},{self.image=}"


class Answer(db.Model):
    answer_id = db.Column(db.Integer, primary_key=True)
    answered_post_id = db.Column(
        db.Integer, db.ForeignKey("post.post_id"), nullable=False
    )
    post_id = db.Column(db.Integer, db.ForeignKey("post.post_id"), nullable=False)


class Liked(db.Model):
    like_id = db.Column(db.Integer, primary_key=True)
    like_hour = db.Column(db.Time)
    like_date = db.Column(db.Date)
    post_id = db.Column(db.Integer, db.ForeignKey("post.post_id"), nullable=False)
    liker_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)


class Chat(db.Model):
    chat_id = db.Column(db.Integer, primary_key=True)
    chat_date = db.Column(db.Date)
    chat_hour = db.Column(db.Time)
    user1_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)


class Message(db.Model):
    message_id = db.Column(db.Integer, primary_key=True)
    message_date = db.Column(db.Date)
    message_hour = db.Column(db.Time)
    post_id = db.Column(db.Integer, db.ForeignKey("post.post_id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    text = db.Column(db.Text)
    image = db.Column(db.LargeBinary)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not session.get("id"):
        return redirect("/")
    if request.method == "POST":
        user_id = request.form.get("id")
        return render_template(
            "profile.html",
            posts=list(
                reversed(
                    db.session.query(Post, User)
                    .join(User, Post.author_id == User.user_id)
                    .filter(User.user_id == user_id)
                    .all()
                )
            )[:100],
            user=User.query.filter_by(user_id=user_id).first(),
        )
    if request.method == "GET":
        return render_template(
            "profile.html",
            posts=list(
                reversed(
                    db.session.query(Post, User)
                    .join(User, Post.author_id == User.user_id)
                    .filter(User.user_id == session["id"])
                    .all()
                )
            )[:100],
            user=User.query.filter_by(user_id=session["id"]).first(),
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
    id = session["id"]
    if id and text:
        new_post = Post(
            post_date=datetime.now().date(),
            post_hour=datetime.now().time(),
            author_id=id,
            text=text,
            image=image,
        )
        db.session.add(new_post)
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
        result = validate_registration(user_data, country_names)
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


def validate_registration(
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
app.run(debug=True)
