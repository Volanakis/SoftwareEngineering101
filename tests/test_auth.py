import pytest
from flask import Blueprint, jsonify

from app import create_app
from app.auth import authenticate, login_required, requires_role
from app.extensions import db
from app.models.user import User


@pytest.fixture
def app_context():
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

    with app.app_context():
        db.create_all()
        user = User(username="carol", full_name="Carol")
        user.set_password("pw")
        db.session.add(user)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_context):
    return app_context.test_client()


def _log_in_as_carol(app_context, client):
    with app_context.app_context():
        user = authenticate("carol", "pw")

    with client.session_transaction() as sess:
        sess["user_id"] = user.id


def test_authenticate_valid_credentials(app_context):
    user = authenticate("carol", "pw")

    assert user is not None
    assert user.username == "carol"


def test_authenticate_invalid_password(app_context):
    assert authenticate("carol", "wrong") is None


def test_authenticate_unknown_user(app_context):
    assert authenticate("nobody", "pw") is None


def test_login_required_rejects_anonymous(client):
    response = client.get("/protected")

    assert response.status_code == 401


def test_login_required_allows_authenticated_user(app_context, client):
    _log_in_as_carol(app_context, client)

    response = client.get("/protected")

    assert response.status_code == 200


def test_requires_role_rejects_visitor(client):
    response = client.get("/users-only")

    assert response.status_code == 403


def test_requires_role_allows_authenticated_user(app_context, client):
    _log_in_as_carol(app_context, client)

    response = client.get("/users-only")

    assert response.status_code == 200
