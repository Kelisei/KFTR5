from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

db = SQLAlchemy()


class User(db.Model):
    """
    Represents a user in the application.

    Attributes:
    - user_id (int): The unique identifier for the user (primary key).
    - username (str): The username of the user (unique, not nullable).
    - email (str): The email address of the user (unique, not nullable).
    - password_hash (str): The hashed password of the user (not nullable).
    - bio (str): The user's biography.
    - website (str): The user's website URL.
    - profile_picture (bytes): Binary data representing the user's profile picture.
    - registration_date (date): The date when the user registered.
    - registration_hour (time): The time when the user registered.
    - country (str): The user's country of residence.
    - approved (bool): Indicates whether the user has been approved (default is False).

    Methods:
    - __repr__(): Returns a string representation of the user for debugging purposes.
    """

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
    """
    Represents the Follows table in the database.

    Attributes:
        follow_id (int): The primary key for the Follows table.
        followed_id (int): The user_id of the user being followed, foreign key referencing 'user.user_id'.
        follower_id (int): The user_id of the follower, foreign key referencing 'user.user_id'.
        follow_date (Date): The date when the follow action occurred.
        follow_hour (Time): The time when the follow action occurred.
    """

    follow_id = db.Column(db.Integer, primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    follower_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    follow_date = db.Column(db.Date)
    follow_hour = db.Column(db.Time)


class Liked(db.Model):
    """
    Represents a 'like' instance in the database.

    Attributes:
        like_id (int): Primary key identifying the like instance.
        like_hour (datetime.time): Time when the like was given.
        like_date (datetime.date): Date when the like was given.
        post_id (int): Foreign key referencing the associated post's ID.
        liker_id (int): Foreign key referencing the user who gave the like.
    """

    like_id = db.Column(db.Integer, primary_key=True)
    like_hour = db.Column(db.Time)
    like_date = db.Column(db.Date)
    post_id = db.Column(db.Integer, db.ForeignKey("post.post_id"), nullable=False)
    liker_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)


class Post(db.Model):
    """
    Represents a post in the application.

    Attributes:
    - post_id (int): The unique identifier for the post.
    - post_date (Date): The date when the post was created.
    - post_hour (Time): The time when the post was created.
    - author_id (int): The user ID of the author who created the post.
    - text (str): The textual content of the post.
    - image (bytes): Binary data representing an optional image attached to the post.

    Methods:
    - __repr__(): Returns a string representation of the Post object for debugging purposes.
    """

    post_id = db.Column(db.Integer, primary_key=True)
    post_date = db.Column(db.Date)
    post_hour = db.Column(db.Time)
    author_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    text = db.Column(db.Text)
    image = db.Column(db.LargeBinary)
    answered_post_id = db.Column(db.Integer, db.ForeignKey("post.post_id"))
    likes = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<Post({self.post_id=},{self.text=},{self.post_hour=},{self.post_date=},{self.author_id=},{self.image=}, {self.answered_post_id=}"


class Answer(db.Model):
    answer_id = db.Column(db.Integer, primary_key=True)
    answered_post_id = db.Column(
        db.Integer, db.ForeignKey("post.post_id"), nullable=False
    )
    post_id = db.Column(db.Integer, db.ForeignKey("post.post_id"), nullable=False)


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
