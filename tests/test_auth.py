import pytest
from flask import Blueprint, jsonify

from app import create_app
from app.auth import authenticate, login_required, requires_role


@pytest.fixture
def app():
    app = create_app("testing")

    bp = Blueprint("test_auth", __name__)

    @bp.get("/protected")
    @login_required
    def protected():
        return jsonify(ok=True)

    @bp.get("/users-only")
    @requires_role("USER")
    def users_only():
        return jsonify(ok=True)

    app.register_blueprint(bp)
    return app


def _log_in(client, user):
    with client.session_transaction() as sess:
        sess["user_id"] = user.id


def test_authenticate_valid_credentials(db, user_factory):
    user_factory(username="carol", password="pw")

    user = authenticate("carol", "pw")

    assert user is not None
    assert user.username == "carol"


def test_authenticate_invalid_password(db, user_factory):
    user_factory(username="carol", password="pw")

    assert authenticate("carol", "wrong") is None


def test_authenticate_unknown_user(db):
    assert authenticate("nobody", "pw") is None


def test_login_required_rejects_anonymous(client):
    response = client.get("/protected")

    assert response.status_code == 401


def test_login_required_allows_authenticated_user(db, user_factory, client):
    user = user_factory()
    _log_in(client, user)

    response = client.get("/protected")

    assert response.status_code == 200


def test_requires_role_rejects_visitor(client):
    response = client.get("/users-only")

    assert response.status_code == 403


def test_requires_role_allows_authenticated_user(db, user_factory, client):
    user = user_factory()
    _log_in(client, user)

    response = client.get("/users-only")

    assert response.status_code == 200
