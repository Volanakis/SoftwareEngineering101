-- Cinema Management Backend — minimal demo seed data.
-- Apply AFTER schema.sql:  sqlite3 instance/cinema.db < sql/seed.sql
--
-- password_hash values below are the werkzeug hash of the literal "password123"
-- (scrypt). Generate your own with:
--   python -c "from werkzeug.security import generate_password_hash as g; print(g('password123'))"

PRAGMA foreign_keys = ON;

INSERT INTO users (id, username, password_hash, full_name) VALUES
    ('11111111-1111-1111-1111-111111111111', 'alice',
     'scrypt:32768:8:1$PLACEHOLDER_REPLACE_ME', 'Alice Programmer'),
    ('22222222-2222-2222-2222-222222222222', 'bob',
     'scrypt:32768:8:1$PLACEHOLDER_REPLACE_ME', 'Bob Submitter'),
    ('33333333-3333-3333-3333-333333333333', 'carol',
     'scrypt:32768:8:1$PLACEHOLDER_REPLACE_ME', 'Carol Staff');

INSERT INTO programs
    (id, name, description, start_date, end_date, creation_date, state, creator_id) VALUES
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Winter Season 2026',
     'Demonstration program', '2026-01-01', '2026-03-31',
     '2026-01-01 09:00:00', 'CREATED',
     '11111111-1111-1111-1111-111111111111');

INSERT INTO program_roles (id, role_type, program_id, user_id) VALUES
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'PROGRAMMER',
     'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
     '11111111-1111-1111-1111-111111111111'),
    ('cccccccc-cccc-cccc-cccc-cccccccccccc', 'STAFF',
     'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
     '33333333-3333-3333-3333-333333333333');
