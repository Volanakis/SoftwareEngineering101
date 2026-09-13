import argparse

from sqlalchemy import inspect, text

from app import create_app
from app.extensions import db
from app.models.user import User


DEMO_PASSWORD = "Demo123!"
DEMO_USERS = (
    ("programmer", "Main Programmer"),
    ("programmer2", "Second Programmer"),
    ("staff", "Cinema Staff"),
    ("submitter", "Film Submitter"),
)


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


def seed_demo_users():
    """Create the exam/demo accounts once without changing existing passwords."""
    users = []
    for username, full_name in DEMO_USERS:
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(username=username, full_name=full_name)
            user.set_password(DEMO_PASSWORD)
            db.session.add(user)
        users.append(user)

    db.session.commit()
    return users


def initialize_database(seed_demo=False):
    app = create_app()

    with app.app_context():
        db.create_all()
        migrate_legacy_schema()
        demo_accounts = (
            [(user.username, user.id) for user in seed_demo_users()]
            if seed_demo
            else []
        )

    print("Database initialized successfully.")
    if demo_accounts:
        print("Demo accounts (local/exam use only):")
        for username, user_id in demo_accounts:
            print(
                f"  {username} | password={DEMO_PASSWORD} | "
                f"id={user_id}"
            )


def parse_args():
    parser = argparse.ArgumentParser(description="Initialize the application database.")
    parser.add_argument(
        "--seed-demo",
        action="store_true",
        help="create idempotent demo accounts for Postman practice",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    initialize_database(seed_demo=args.seed_demo)
