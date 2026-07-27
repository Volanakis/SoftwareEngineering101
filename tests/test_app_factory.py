def test_create_app_returns_flask_app(app):
    assert app is not None
    assert app.name == "app"


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
