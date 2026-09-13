from pathlib import Path
import uuid

from sqlalchemy import inspect, text

from app import create_app
from app.extensions import db
from app.models.user import User
from init_db import DEMO_PASSWORD, DEMO_USERS, migrate_legacy_schema, seed_demo_users


def test_database_initialization():
    app = create_app("testing")

    with app.app_context():
        db.create_all()

        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        assert "users" in tables
        assert "programs" in tables
        assert "program_roles" in tables
        assert "screenings" in tables


def test_demo_seed_creates_users_and_is_idempotent(db):
    first_seed = seed_demo_users()
    first_ids = {user.username: user.id for user in first_seed}

    second_seed = seed_demo_users()

    assert User.query.count() == len(DEMO_USERS)
    assert {user.username: user.id for user in second_seed} == first_ids
    assert all(user.check_password(DEMO_PASSWORD) for user in second_seed)


def test_legacy_database_gets_creator_column(monkeypatch):
    database_file = Path("instance") / f"legacy-{uuid.uuid4().hex}.db"
    database_path = database_file.resolve().as_posix()
    monkeypatch.setenv("TEST_DATABASE_URL", f"sqlite:///{database_path}")
    app = create_app("testing")

    try:
        with app.app_context():
            with db.engine.begin() as connection:
                connection.execute(
                    text(
                        "CREATE TABLE programs ("
                        "id VARCHAR(36) PRIMARY KEY, name VARCHAR(120) UNIQUE NOT NULL, "
                        "description TEXT NOT NULL, start_date DATE NOT NULL, "
                        "end_date DATE NOT NULL, creation_date DATETIME NOT NULL, "
                        "state VARCHAR(32) NOT NULL)"
                    )
                )

            db.create_all()
            assert "creator_id" not in {
                column["name"] for column in inspect(db.engine).get_columns("programs")
            }

            migrate_legacy_schema()

            assert "creator_id" in {
                column["name"] for column in inspect(db.engine).get_columns("programs")
            }
            db.session.remove()
            db.engine.dispose()
    finally:
        database_file.unlink(missing_ok=True)
