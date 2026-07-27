import uuid

import pytest

from app import create_app
from app.extensions import db as _db
from app.models.user import User


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def user_factory(db):
    def make_user(username=None, password="password123", full_name="Test User"):
        if username is None:
            username = f"user-{uuid.uuid4().hex[:8]}"

        user = User(username=username, full_name=full_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    return make_user
