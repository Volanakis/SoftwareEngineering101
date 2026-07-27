import pytest
from sqlalchemy.exc import IntegrityError

from app import create_app
from app.extensions import db
from app.models.user import User


@pytest.fixture
def app_context():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_set_password_hashes_the_password(app_context):
    user = User(username="alice", full_name="Alice Doe")
    user.set_password("s3cret")

    assert user.password_hash != "s3cret"
    assert user.check_password("s3cret") is True
    assert user.check_password("wrong") is False


def test_id_is_generated_automatically(app_context):
    user = User(username="dave", full_name="Dave")
    user.set_password("pw")
    db.session.add(user)
    db.session.commit()

    assert user.id is not None


def test_username_must_be_unique(app_context):
    user1 = User(username="bob", full_name="Bob")
    user1.set_password("pw")
    db.session.add(user1)
    db.session.commit()

    user2 = User(username="bob", full_name="Bob Two")
    user2.set_password("pw2")
    db.session.add(user2)

    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
