from flask import Flask
from app.main.extensions import db, jwt, migrate, ma
from app.main.routes import register_blueprints
from app.errors.handlers import register_error_handlers
from app.config import Config
import logging
from logging.handlers import RotatingFileHandler
import os
from app.commands import create_superuser


def configure_logging(app):
    if not os.path.exists('logs'):
        os.mkdir('logs')

    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    file_handler.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Logging initialized')


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    configure_logging(app)

    # Инициализация расширений
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    # Blueprint'ы
    register_blueprints(app)

    # Глобальные ошибки
    register_error_handlers(app)

    app.cli.add_command(create_superuser)

    return app
