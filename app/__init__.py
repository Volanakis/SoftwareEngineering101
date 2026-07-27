from flask import Flask


def create_app(config_object=None):
    app = Flask(__name__)

    if config_object is not None:
        app.config.from_object(config_object)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
