from flask import Flask
from app.main.extensions import db, migrate, jwt, ma
from app.main.routes import register_blueprints
from app.errors.handlers import register_error_handlers
from app.config import Config
from dotenv import load_dotenv


def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)

    register_blueprints(app)
    register_error_handlers(app)

    return app
