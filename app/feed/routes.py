from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    session,
    url_for,
    jsonify,
    abort,
)
from ..model import Post, Liked, db, bcrypt, User, Follows

from ..utils import (
    is_logged,
    user_info,
    user_exists,
    get_follow,
    EMAIL_PATTERN,
    make_pfp,
    optimize_image,
    user_posts,
)

import base64
from datetime import datetime

feed_bp = Blueprint("feed", __name__)


@feed_bp.route("/<int:post_id>/like", methods=["POST"])
def like(post_id: int):
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


@feed_bp.route("/<int:post_id>/see", methods=["GET"])
def see_post(post_id: int):
    if is_logged():

        post = (
            db.session.query(Post, User)
            .join(User, Post.author_id == User.user_id)
            .filter(Post.post_id == post_id)
            .first()
        )
        if bool(post):
            replies = (
                db.session.query(Post, User)
                .join(User, Post.author_id == User.user_id)
                .filter(Post.answered_post_id == post_id)
                .all()
            )
            replied = (
                db.session.query(Post, User)
                .join(User, Post.author_id == User.user_id)
                .filter(Post.post_id == post[0].answered_post_id)
                .first()
            )
            return render_template(
                "post_view.html", post=post, posts=replies, replied=replied
            )
    return redirect("/")


@feed_bp.route("/ownprofile", methods=["GET", "POST"])
def ownprofile():
    """Redirect to the profile of the currentyly logged user (with post
    request) or goes to login."""
    if is_logged():
        return redirect(
            url_for(
                "feed.profile",
                username=User.query.filter_by(user_id=session.get("id"))
                .first()
                .username,
            )
        )
    return redirect("/login")


@feed_bp.route("/follow/<username>", methods=["POST"])
def follow(username: str):
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
        return redirect(url_for("feed.profile", username=username))
    redirect("/")


@feed_bp.route("/<username>/edit", methods=["POST"])
def edit_profile(username: str):
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
            return redirect(url_for("feed.profile", username=username))
    return redirect("/")


@feed_bp.route("/<username>", methods=["GET"])
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


@feed_bp.route("/", methods=["GET", "POST"])
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


@feed_bp.route("/new_post", methods=["POST"])
def new_post():
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
        return render_template(
            "post.html",
            post=user_post,
            user=User.query.filter_by(user_id=session.get("id")).first(),
        )
    return jsonify({"status": "error", "message": "Invalid session or empty text"})
