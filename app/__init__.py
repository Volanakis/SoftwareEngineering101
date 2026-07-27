import os

from dotenv import load_dotenv
from flask import Flask

from config import config_by_name

load_dotenv()


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    from app.extensions import db

    db.init_app(app)

    from app import models  # noqa: F401  (registers models on db.metadata)

    from app.blueprints.programs import programs_bp

    app.register_blueprint(programs_bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
