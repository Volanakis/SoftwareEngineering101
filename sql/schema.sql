-- Cinema Management Backend — relational schema
-- =============================================
-- Hand-written DDL for the four tables backing the system (class diagram `05`).
-- Kept in sync with the SQLAlchemy models in app/models/ (see tests/test_sql_schema.py).
-- Dialect: SQLite (dev/test). For PostgreSQL, replace DATETIME -> TIMESTAMP and
-- BOOLEAN default 0 -> FALSE; everything else is portable.
--
-- Apply:   sqlite3 instance/cinema.db < sql/schema.sql
-- Reset:   sqlite3 instance/cinema.db < sql/drop_all.sql
-- The Python equivalent is `python init_db.py` (SQLAlchemy create_all()).

PRAGMA foreign_keys = ON;

-- ΛΑ-1.1 / ΜΛΑ-3.1: shared Users table (also read by the external User Management System).
CREATE TABLE IF NOT EXISTS users (
    id            VARCHAR(36)  NOT NULL,
    username      VARCHAR(80)  NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(120) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (username)
);

-- ΛΑ-2: Program (season). `state` follows the 8-value lifecycle (ΛΑ-2.8).
CREATE TABLE IF NOT EXISTS programs (
    id            VARCHAR(36)  NOT NULL,
    name          VARCHAR(120) NOT NULL,
    description   TEXT         NOT NULL,
    start_date    DATE         NOT NULL,
    end_date      DATE         NOT NULL,
    creation_date DATETIME     NOT NULL,
    state         VARCHAR(16)  NOT NULL,
    creator_id    VARCHAR(36),
    PRIMARY KEY (id),
    UNIQUE (name),
    FOREIGN KEY (creator_id) REFERENCES users (id),
    CHECK (state IN (
        'CREATED', 'SUBMISSION', 'ASSIGNMENT', 'REVIEW',
        'SCHEDULING', 'FINAL_SUBMISSION', 'DECISION', 'ANNOUNCED'
    ))
);

-- ΛΑ-1.5: join entity User <-> Program, at most one role per (program, user).
CREATE TABLE IF NOT EXISTS program_roles (
    id         VARCHAR(36) NOT NULL,
    role_type  VARCHAR(10) NOT NULL,
    program_id VARCHAR(36) NOT NULL,
    user_id    VARCHAR(36) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_program_roles_program_user UNIQUE (program_id, user_id),
    FOREIGN KEY (program_id) REFERENCES programs (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id),
    CHECK (role_type IN ('PROGRAMMER', 'STAFF'))
);

-- ΛΑ-3: Screening. `submitter_id` is the implicit SUBMITTER (ΛΑ-1.6, not a program_role).
-- `handler_id` is the assigned STAFF, NULL until the ASSIGNMENT phase (ΛΑ-3.5).
CREATE TABLE IF NOT EXISTS screenings (
    id                    VARCHAR(36)  NOT NULL,
    creation_date         DATETIME     NOT NULL,
    state                 VARCHAR(9)   NOT NULL,
    program_id            VARCHAR(36)  NOT NULL,
    submitter_id          VARCHAR(36)  NOT NULL,
    handler_id            VARCHAR(36),
    film_title            VARCHAR(255) NOT NULL,
    film_cast             TEXT,
    film_genres           TEXT,
    film_duration_minutes INTEGER,
    auditorium_name       VARCHAR(255),
    start_time            DATETIME,
    end_time              DATETIME,
    review_score          FLOAT,
    review_comments       TEXT,
    rejection_reason      TEXT,
    final_submitted       BOOLEAN      NOT NULL DEFAULT 0,
    approval_notes        TEXT,
    PRIMARY KEY (id),
    FOREIGN KEY (program_id) REFERENCES programs (id) ON DELETE CASCADE,
    FOREIGN KEY (submitter_id) REFERENCES users (id),
    FOREIGN KEY (handler_id) REFERENCES users (id),
    CHECK (state IN (
        'CREATED', 'SUBMITTED', 'REVIEWED', 'APPROVED', 'SCHEDULED', 'REJECTED'
    ))
);

-- Search-supporting indexes (ΛΑ-2.5, ΛΑ-3.11).
CREATE INDEX IF NOT EXISTS ix_program_roles_program ON program_roles (program_id);
CREATE INDEX IF NOT EXISTS ix_program_roles_user    ON program_roles (user_id);
CREATE INDEX IF NOT EXISTS ix_screenings_program    ON screenings (program_id);
CREATE INDEX IF NOT EXISTS ix_screenings_submitter  ON screenings (submitter_id);
CREATE INDEX IF NOT EXISTS ix_screenings_start_time ON screenings (start_time);
