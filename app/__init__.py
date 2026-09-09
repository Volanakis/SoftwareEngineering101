import os

from dotenv import load_dotenv
from flask import Flask

from config import config_by_name
from app.logging_config import configure_logging

load_dotenv()


def create_app(config_name=None):
    config_name = (
        config_name
        or os.environ.get(
            "FLASK_ENV",
            "development",
        )
    )

    app = Flask(__name__)

    app.config.from_object(
        config_by_name[config_name]
    )

    configure_logging(app)

    from app.extensions import db, limiter

    db.init_app(app)
    limiter.init_app(app)

    from app import models  # noqa: F401

    from app.blueprints.programs import programs_bp
    from app.blueprints.screenings import screenings_bp

    app.register_blueprint(
        programs_bp
    )

    app.register_blueprint(
        screenings_bp
    )

    @app.get("/health")
    def health():
        return {
            "status": "ok"
        }

    return app