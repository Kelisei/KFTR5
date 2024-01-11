from flask import session
from io import BytesIO
from PIL import Image
import requests
import re
from datetime import datetime
import base64
from src.model import User, Post, Follows, db

EMAIL_PATTERN = re.compile(r"[^@]+@[^@]+\.[^@]+")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
SUCCESSFUL = 200

def is_allowed_format(filename: str) -> bool:
    """Checks if the image has the accepted format.

    Args:
        filename (str): Name of the file.

    Returns:
        bool: True if it's a png, jpg, jpeg, or gif.
    """
    return False if "." not in filename else filename.split(".")[-1].lower() in ALLOWED_EXTENSIONS


def make_pfp(image_binary: bytes, size: int, format="WebP") -> bytes:
    """Makes the received image squared and converts it to WebP

    Args:
        image_binary (bytes): Image information.
        size (int): Size of the sides of the square.

    Returns:
        bytes: WebP image in binary format
    """
    image = Image.open(BytesIO(image_binary)).resize((size, size))
    image_buffer = BytesIO()
    image.save(image_buffer, format=format)
    return image_buffer.getvalue()

def optimize_image(image_binary: bytes, format="WebP", quality=40) -> bytes:
    image = Image.open(BytesIO(image_binary))
    image_buffer = BytesIO()
    image.save(image_buffer, format=format, quality=quality)
    return image_buffer.getvalue()

def get_country_names(lower: bool) -> list[str]:
    """Gets the country names from source and returns a list with all
    the country names, or a list with only Argentina in it.

    Args:
        lower (bool): Get the names on lower case.

    Returns:
        list[str]: List of country names.
    """
    response = requests.get("https://restcountries.com/v2/all")
    if response.status_code == SUCCESSFUL:
        return [
            country["name"].lower() if lower else country["name"]
            for country in response.json()
        ]
    return ["argentina" if lower else "Argentina"]    

def process_registration(user_data: dict):
    """
    Processes the user registration data.

    Args:
        user_data (dict): A dictionary containing the user registration data.

    Returns:
        None
    """

    image_binary = base64.b64encode(utils.make_pfp(user_data["image"].read(), 300))
    password_hash = bcrypt.generate_password_hash(password=user_data["password"])
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


def validate_user_info(user_data: dict, country_names: list[str]) -> tuple[bool, str]:
    """
    Validates the user registration data.

    Args:
    Args:
        user_data (dict): A dictionary containing the user registration data.

    Returns:
        tuple(bool, str): A tuple indicating if the validation passed or not, and an error message if any validation fails.
    """

    if not user_data["username"] or len(user_data["username"]) > 30:
        return (True, "Pick a username with a length between 1 and 30 characters")
    if User.query.filter_by(username=user_data["username"]).first():
        return (True, "That username already exists")
    if not user_data["email"] or not utils.email_pattern.match(user_data["email"]):
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


def user_exists(username: str) -> bool:
    """
    Returns if that id corresponds to a user stored
    in the database, if the id is null then returns false.
    """
    return bool(User.query.filter_by(username=username).first())


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
    
def is_logged() -> bool:
    return bool(session.get("id"))

