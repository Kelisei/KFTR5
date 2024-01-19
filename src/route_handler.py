from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    url_for,
    jsonify,
    session,
)
from flask_session import Session
from flask_migrate import Migrate
from flask_cors import CORS
from src.utils import (
    validate_user_info,
    user_exists,
    process_registration,
    user_info,
    user_posts,
    get_follow,
    is_logged,
    EMAIL_PATTERN,
    optimize_image,
    make_pfp,
    get_country_names,
)
from datetime import datetime
import base64
from datetime import timedelta
from werkzeug.middleware.proxy_fix import ProxyFix
import os
from src.model import (
    db,
    bcrypt,
    User,
    Post,
    Follows,
    Liked,
)


class RouteHandler:
    def __init__(self, application) -> None:
        self.app = application
        self.setup()

    def setup(self):
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"
        self.app.config["SESSION_PERMANENT"] = False
        self.app.secret_key = os.environ.get("SECRET_KEY")
        self.app.config["SESSION_TYPE"] = "filesystem"
        self.app.config["SESSION_PERMANENT"] = True
        self.app.permanent_session_lifetime = timedelta(weeks=1)
        self.app.wsgi_app = ProxyFix(self.app.wsgi_app)

        Session(self.app)
        bcrypt.init_app(self.app)
        db.init_app(self.app)
        Migrate(self.app, db)
        CORS(self.app)

        self.register_routes()

    def register_routes(self):
        self.app.errorhandler(404)(self.page_not_found)
        self.app.route("/<int:post_id>/like", methods=["POST"])(self.like)
        self.app.route("/<int:post_id>/see", methods=["GET"])(self.see_post)
        self.app.route("/ownprofile", methods=["GET", "POST"])(self.ownprofile)
        self.app.route("/follow/<username>", methods=["POST"])(self.follow)
        self.app.route("/<username>/edit", methods=["POST"])(self.edit_profile)
        self.app.route("/<username>", methods=["GET"])(self.profile)
        self.app.route("/", methods=["GET", "POST"])(self.feed)
        self.app.route("/new_post", methods=["POST"])(self.new_post)
        self.app.route("/login", methods=["GET", "POST"])(self.login)
        self.app.route("/register", methods=["GET", "POST"])(self.register)

    def initialize_db(self):
        with self.app.app_context():
            db.create_all()

    def run(self, debug=False):
        self.app.run(debug=debug)

    def page_not_found(self, error):
        return render_template("page_not_found.html", error=error), 404

    def like(self, post_id: int):
        if is_logged():
            username = request.form.get("username")
            data = user_info(username)
            post = Post.query.filter_by(post_id=post_id).first()
            if bool(data):
                new_like = Liked.query.filter_by(
                    post_id=post_id, liker_id=data.user_id
                ).first()
                if bool(new_like):
                    post.likes -= 1
                    db.session.delete(new_like)
                else:
                    new_like = Liked(
                        like_hour=datetime.now().time(),
                        like_date=datetime.now().date(),
                        post_id=post_id,
                        liker_id=data.user_id,
                    )
                    post.likes += 1
                    db.session.add(new_like)
                db.session.commit()
            return f"{post.likes}"
        abort(404)

    def see_post(self, post_id: int):
        if is_logged():
            post = Post.query.filter_by(post_id=post_id).first()
            if bool(post):
                replies = Post.query.filter_by(answered_post_id=post_id)
                replied = Post.query.filter_by(post_id=post.answered_post_id)
                return render_template(
                    "post.html", post=post, replies=replies, replied=replied
                )
        return redirect("/")

    def ownprofile(self):
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

    def follow(self, username: str):
        if is_logged():
            if user_exists(username):
                followed_id = user_info(username).user_id
                new_follow = get_follow(followed_id, session.get("id"))
                if not bool(new_follow):
                    new_follow = Follows(
                        followed_id=followed_id,
                        follower_id=session.get("id"),
                        follow_date=datetime.now().date(),
                        follow_hour=datetime.now().time(),
                    )
                    db.session.add(new_follow)
                else:
                    db.session.delete(new_follow)
                db.session.commit()
            return redirect(url_for("profile", username=username))
        redirect("/")

    def edit_profile(self, username: str):
        if user_exists(username) and is_logged():
            profile_info = user_info(username)
            if session.get("id") == profile_info.user_id:
                new_username = request.form.get("username")
                if bool(new_username) or len(new_username) <= 30:
                    username = new_username
                    profile_info.username = new_username
                new_email = request.form.get("email")
                if bool(new_email) or EMAIL_PATTERN.match(new_email):
                    profile_info.email = new_email
                new_bio = request.form.get("bio")
                if bool(new_bio) and len(new_bio) < 256:
                    profile_info.bio = new_bio
                new_website = request.form.get("website")
                if bool(new_website) and len(new_website) < 256:
                    profile_info.website = new_website
                pfp = request.files.get("pfp").read()
                if bool(pfp):
                    pfp = base64.b64encode(make_pfp(pfp, 300))
                    profile_info.profile_picture = pfp
                print(profile_info)
                db.session.commit()
                return redirect(url_for("profile", username=username))
        return redirect("/")

    def profile(self, username):
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

    def feed(self):
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

    def new_post(self):
        text = request.form.get("text")
        image = request.files.get("image")
        if image:
            image = base64.b64encode(optimize_image(image.read()))
        else:
            image = None
        current_session_id = session.get("id")
        if current_session_id and text:
            user_post = Post(
                post_date=datetime.now().date(),
                post_hour=datetime.now().time(),
                author_id=current_session_id,
                text=text,
                image=image,
                answered_post_id=request.form.get("answered_post_id"),
            )
            db.session.add(user_post)
            db.session.commit()
            return render_template("post.html", post=user_post, user=User.query.filter_by(user_id=session.get("id")).first())
        return jsonify({"status": "error", "message": "Invalid session or empty text"})

    def login(self):
        if session.get("id"):
            redirect("/")
        if request.method == "GET":
            return render_template("login.html", message="")
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            user = User.query.filter_by(email=email).first()
            if user and bcrypt.check_password_hash(
                pw_hash=user.password_hash, password=password
            ):
                session["id"] = user.user_id
                return redirect("/")
            return render_template("login.html", message="Invalid email or password")

    def register(self):
        if session.get("id"):
            redirect("/")
        country_names = get_country_names(lower=False)
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


if __name__ == "__main__":
    app = Flask(__name__)
    rh = RouteHandler(app)
    rh.run()
