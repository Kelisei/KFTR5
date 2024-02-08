import os
from datetime import timedelta

from flask_cors import CORS
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix

import src.routes as routes
from flask_session import Session
from src.model import bcrypt, db


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
        self.app.errorhandler(404)(routes.page_not_found)
        self.app.route("/<int:post_id>/like", methods=["POST"])(routes.like)
        self.app.route("/<int:post_id>/see", methods=["GET"])(routes.see_post)
        self.app.route("/ownprofile", methods=["GET", "POST"])(routes.ownprofile)
        self.app.route("/follow/<username>", methods=["POST"])(routes.follow)
        self.app.route("/<username>/edit", methods=["POST"])(routes.edit_profile)
        self.app.route("/<username>", methods=["GET"])(routes.profile)
        self.app.route("/", methods=["GET", "POST"])(routes.feed)
        self.app.route("/new_post", methods=["POST"])(routes.new_post)
        self.app.route("/login", methods=["GET", "POST"])(routes.login)
        self.app.route("/register", methods=["GET", "POST"])(routes.register)

    def initialize_db(self):
        with self.app.app_context():
            db.create_all()

    def run(self, debug=False):
        self.app.run(debug=debug)
