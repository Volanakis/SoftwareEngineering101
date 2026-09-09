from sqlalchemy import inspect

from app import create_app
from app.extensions import db


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