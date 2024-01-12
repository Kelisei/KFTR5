from flask import Flask
from src.route_handler import RouteHandler

if __name__ == "__main__":
    app = Flask(__name__)
    router = RouteHandler(application=app)
    router.initialize_db()
    router.run(debug=True)
