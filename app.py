from flask import Flask

from src.route_handler import RouteHandler

# TODO -> add ability to answer your own recently posted posts.
# TODO -> Post page (see respondant post and responding posts).
if __name__ == "__main__":
    app = Flask(__name__)
    router = RouteHandler(application=app)
    router.initialize_db()
    router.run(debug=True)
