from flask import Blueprint, redirect, render_template, request, session
from ..model import User, bcrypt
from ..utils import get_country_names, validate_user_info, process_registration

login_bp = Blueprint("login", __name__)


@login_bp.route("/login", methods=["GET", "POST"])
def login():
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


@login_bp.route("/register", methods=["GET", "POST"])
def register():
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
