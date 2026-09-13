from app import create_app
from app.extensions import db
from sqlalchemy import inspect, text


def migrate_legacy_schema():
    """Apply the small backwards-compatible migration needed by final-fixes."""
    inspector = inspect(db.engine)
    if "programs" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("programs")}
    if "creator_id" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE programs ADD COLUMN creator_id VARCHAR(36) "
                "REFERENCES users(id)"
            )
        )
        db.session.execute(
            text(
                "UPDATE programs SET creator_id = ("
                "SELECT user_id FROM program_roles "
                "WHERE program_roles.program_id = programs.id "
                "AND role_type = 'PROGRAMMER' LIMIT 1"
                ") WHERE creator_id IS NULL"
            )
        )
        db.session.commit()


def initialize_database():
    app = create_app()

    with app.app_context():
        db.create_all()
        migrate_legacy_schema()

    print("Database initialized successfully.")


if __name__ == "__main__":
    initialize_database()
