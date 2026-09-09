"""Validates sql/schema.sql and keeps it in sync with the SQLAlchemy models.

Runs the hand-written DDL against a throwaway SQLite database and checks that
every table/column the ORM defines is present with matching nullability.
"""

import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import inspect

from app import create_app
from app.extensions import db

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


@pytest.fixture
def sql_conn():
    conn = sqlite3.connect(":memory:")
    conn.executescript((SQL_DIR / "schema.sql").read_text())
    yield conn
    conn.close()


def _columns(conn, table):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    # name -> notnull (1/0)
    return {row[1]: row[3] for row in rows}


def test_schema_sql_creates_all_tables(sql_conn):
    tables = {
        row[0]
        for row in sql_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    assert {"users", "programs", "program_roles", "screenings"} <= tables


def test_schema_sql_matches_orm_models(sql_conn):
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)

        for table in ("users", "programs", "program_roles", "screenings"):
            orm_cols = {col["name"]: col["nullable"] for col in inspector.get_columns(table)}
            sql_cols = _columns(sql_conn, table)

            assert set(orm_cols) == set(sql_cols), f"column mismatch in {table}"

            for name, orm_nullable in orm_cols.items():
                sql_notnull = bool(sql_cols[name])
                assert sql_notnull == (not orm_nullable), (
                    f"{table}.{name} nullability differs between schema.sql and the model"
                )


def test_schema_sql_enforces_enum_check_constraints(sql_conn):
    sql_conn.execute(
        "INSERT INTO users (id, username, password_hash, full_name) "
        "VALUES ('u1', 'u1', 'x', 'U One')"
    )
    with pytest.raises(sqlite3.IntegrityError):
        sql_conn.execute(
            "INSERT INTO programs "
            "(id, name, description, start_date, end_date, creation_date, state) "
            "VALUES ('p1', 'P1', 'd', '2026-01-01', '2026-02-01', "
            "'2026-01-01 00:00:00', 'NOT_A_STATE')"
        )


def test_drop_all_sql_removes_tables(sql_conn):
    sql_conn.executescript((SQL_DIR / "drop_all.sql").read_text())
    tables = {
        row[0]
        for row in sql_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    assert not ({"users", "programs", "program_roles", "screenings"} & tables)
