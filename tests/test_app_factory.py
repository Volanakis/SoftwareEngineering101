def test_create_app_returns_flask_app(app):
    assert app is not None
    assert app.name == "app"


def test_create_app_loads_testing_config(app):
    assert app.config["TESTING"] is True
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"


def test_create_app_defaults_to_development_config():
    from app import create_app

    app = create_app()

    assert app.config["DEBUG"] is True
    assert app.config["TESTING"] is False


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
