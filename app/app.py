import os
from flask import Flask
from .model import db, bcrypt
from flask_cors import CORS
from flask_migrate import Migrate
from flask_session import Session

from .log_in.routes import login_bp
from .feed.routes import feed_bp
from datetime import timedelta



def create_app() -> Flask:
    app = Flask(__name__)

    # Configuración de la base de datos
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"

    # Configuración de la sesión
    app.config["SESSION_PERMANENT"] = False
    app.secret_key = os.environ.get("SECRET_KEY")
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = True
    app.permanent_session_lifetime = timedelta(weeks=1)

    # Inicialización de extensiones
    Session(app)
    bcrypt.init_app(app)
    db.init_app(app)
    Migrate(app, db)
    CORS(app)
    
    # Registro de blueprints
    app.register_blueprint(login_bp)
    app.register_blueprint(feed_bp)

    return app

