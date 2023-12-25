from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
import re
import utils

email_pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"
app.config["SESSION_PERMANENT"] = False
app.secret_key = "KeliseiVenturaPerronsio1GokuVegetta777"
app.config["SESSION_TYPE"] = "filesystem"
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
        return f"<User(user_id={self.user_id}, username={self.username}, email={self.email}, bio={self.bio}, website={self.website}, country={self.country}, approved={self.approved})>"


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


@app.route("/")
def feed():
    print(User.query.all())
    if session.get("id"):
        return render_template("feed.html")
    return redirect("/login")


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
        username = request.form.get("username")
        if len(username) == 0 or len(username) > 30:
            return render_template(
                "register.html",
                message="Pick a username with a length between 1 and 30 characters",
            )
        email = request.form.get("email")
        if len(email) == 0 or not email_pattern.match(email):
            return render_template(
                "register.html",
                message="Please enter a valid email, i.e: example@gmail.com",
            )
        password = request.form.get("password")
        if len(password) < 7 or len(password) > 30 or not re.search(r"\d", password):
            return render_template(
                "register.html",
                message="Please enter a valid password (minimum 6 characters, should contain a number)",
            )
        country = request.form.get("country")
        if country not in country_names:
            return render_template(
                "register.html",
                message="Invalid country name",
            )
        image = request.files.get("image")
        if not image:
            return render_template(
                "register.html",
                message="Profile picture not loaded",
                countries=country_names
            )
        if not utils.is_allowed_format(image.filename):
            return render_template(
                "register.html",
                message="Introduce a valid image (png, jpg, gif)",
                countries=country_names
            )
        image_binary = utils.make_pfp(image.read(), 300)
        password_hash = bcrypt.generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            profile_picture=image_binary,
            country=country,
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect("/")

with app.app_context():
    db.drop_all()
    db.create_all()

app.run(debug=True)
