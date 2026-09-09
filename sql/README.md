# SQL scripts — database creation

Hand-written DDL for the Cinema Management Backend, kept in sync with the
SQLAlchemy models in `app/models/` (class diagram `05`). Verified by
`tests/test_sql_schema.py`, which runs `schema.sql` against a fresh SQLite
database and asserts every table/column the ORM expects.

| File | Purpose |
|---|---|
| `schema.sql`   | Create the 4 tables (`users`, `programs`, `program_roles`, `screenings`) + search indexes + `CHECK` constraints for the state/role enums. |
| `drop_all.sql` | Drop the 4 tables in reverse-dependency order. |
| `seed.sql`     | Optional minimal demo data (replace the placeholder password hashes first). |

## Usage

```bash
# fresh database
sqlite3 instance/cinema.db < sql/schema.sql

# wipe and recreate
sqlite3 instance/cinema.db < sql/drop_all.sql
sqlite3 instance/cinema.db < sql/schema.sql

# optional demo rows
sqlite3 instance/cinema.db < sql/seed.sql
```

The Python equivalent is `python init_db.py` (calls `db.create_all()`); it and
`schema.sql` produce the same structure. Use `init_db.py` for local dev, the SQL
scripts when provisioning a database outside the app (CI, DBA hand-off, the
report's deliverables).

## Dialect notes

Written for **SQLite** (the dev/test database). For **PostgreSQL**:

- `DATETIME` → `TIMESTAMP`
- `BOOLEAN NOT NULL DEFAULT 0` → `... DEFAULT FALSE`
- `PRAGMA foreign_keys = ON;` is unnecessary (FKs enforced by default)
