import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User


def test_set_password_hashes_the_password(user_factory):
    user = user_factory(password="s3cret")

    assert user.password_hash != "s3cret"
    assert user.check_password("s3cret") is True
    assert user.check_password("wrong") is False


def test_id_is_generated_automatically(user_factory):
    user = user_factory()

    assert user.id is not None


def test_username_must_be_unique(db, user_factory):
    user_factory(username="bob")

    duplicate = User(username="bob", full_name="Bob Two")
    duplicate.set_password("pw2")
    db.session.add(duplicate)

    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
