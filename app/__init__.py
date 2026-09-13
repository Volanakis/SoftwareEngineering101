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
    from app.blueprints.auth import auth_bp

    app.register_blueprint(auth_bp)

    app.register_blueprint(
        programs_bp
    )

    app.register_blueprint(
        screenings_bp
    )

    @app.errorhandler(404)
    def not_found(_error):
        return {"error": "Resource not found"}, 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return {"error": "Method not allowed"}, 405

    @app.errorhandler(429)
    def rate_limit_exceeded(_error):
        return {"error": "Rate limit exceeded"}, 429

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.exception("Unhandled server error", exc_info=error)
        return {"error": "Internal server error"}, 500

    @app.get("/health")
    def health():
        return {
            "status": "ok"
        }

    return app
