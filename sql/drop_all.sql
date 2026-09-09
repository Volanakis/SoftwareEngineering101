-- Cinema Management Backend — drop all tables (reverse dependency order).
-- Apply: sqlite3 instance/cinema.db < sql/drop_all.sql

PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS screenings;
DROP TABLE IF EXISTS program_roles;
DROP TABLE IF EXISTS programs;
DROP TABLE IF EXISTS users;
