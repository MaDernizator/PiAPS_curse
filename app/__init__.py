from flask import Flask
from app.main.extensions import db, jwt, migrate, ma
from app.main.routes import register_blueprints
from app.errors.handlers import register_error_handlers
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Инициализация расширений
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    # Blueprint'ы
    register_blueprints(app)

    # Глобальные ошибки
    register_error_handlers(app)

    return app