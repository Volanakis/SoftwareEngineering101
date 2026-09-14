# ER Diagram (Analytic) — Relational Schema

Αναλυτικό Entity-Relationship diagram σε επίπεδο **γνησίων relational πινάκων** (PK/FK/UK, τύποι στηλών, cardinalities), σε αντίθεση με το `05-class-diagram.md` που δείχνει τις πληροφοριακές οντότητες σε επίπεδο UML/domain model. Πηγή αλήθειας: `sql/schema.sql` (τηρείται συγχρονισμένο με τα SQLAlchemy models του `app/models/` μέσω `tests/test_sql_schema.py`).

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif', 'background':'#ffffff', 'primaryColor':'#dbeafe', 'primaryBorderColor':'#2563eb', 'primaryTextColor':'#1e3a8a', 'lineColor':'#64748b'}}}%%
erDiagram
    USERS {
        string id PK "UUID"
        string username UK "NOT NULL"
        string password_hash "NOT NULL"
        string full_name "NOT NULL"
    }

    PROGRAMS {
        string id PK "UUID"
        string name UK "NOT NULL"
        string description "NOT NULL"
        date start_date "NOT NULL"
        date end_date "NOT NULL"
        datetime creation_date "NOT NULL, auto"
        string state "NOT NULL, CHECK 8 values"
        string creator_id FK "nullable"
    }

    PROGRAM_ROLES {
        string id PK "UUID"
        string role_type "NOT NULL, CHECK PROGRAMMER|STAFF"
        string program_id FK "NOT NULL, ON DELETE CASCADE"
        string user_id FK "NOT NULL"
    }

    SCREENINGS {
        string id PK "UUID"
        datetime creation_date "NOT NULL, auto"
        string state "NOT NULL, CHECK 6 values"
        string program_id FK "NOT NULL, ON DELETE CASCADE"
        string submitter_id FK "NOT NULL"
        string handler_id FK "nullable, until ASSIGNMENT"
        string film_title "NOT NULL"
        string film_cast
        string film_genres
        int film_duration_minutes
        string auditorium_name
        datetime start_time
        datetime end_time
        float review_score
        string review_comments
        string rejection_reason
        boolean final_submitted "NOT NULL, default false"
        string approval_notes
    }

    USERS    |o--o{ PROGRAMS       : "creates (creator_id)"
    USERS    ||--o{ PROGRAM_ROLES  : holds
    PROGRAMS ||--o{ PROGRAM_ROLES  : "assigned via"
    PROGRAMS ||--o{ SCREENINGS     : contains
    USERS    ||--o{ SCREENINGS     : "submits (submitter_id)"
    USERS    |o--o{ SCREENINGS     : "handles (handler_id)"
```

## Σημειώσεις

- **`PROGRAM_ROLES`** είναι ο πίνακας σύνδεσης (join table) της many-to-many σχέσης `USERS` ↔ `PROGRAMS`, με επιπλέον composite unique constraint `UNIQUE (program_id, user_id)` — το πολύ ένας ρόλος ανά ζεύγος (χρήστης, πρόγραμμα). Ο τύπος ρόλου (`PROGRAMMER` / `STAFF`) περιορίζεται με `CHECK`.
- Ο ρόλος **SUBMITTER δεν αποθηκεύεται** στο `PROGRAM_ROLES` — προκύπτει έμμεσα από το FK `screenings.submitter_id` (βλ. παραδοχή §0.4 στο `README.md`), γι' αυτό εμφανίζεται εδώ ως ξεχωριστή σχέση `USERS ||--o{ SCREENINGS : submits`, ανεξάρτητη από το `PROGRAM_ROLES`.
- `programs.creator_id` και `screenings.handler_id` είναι **nullable** FKs (χωρίς `ON DELETE CASCADE`) → προαιρετική συμμετοχή (`|o`) στην πλευρά `USERS`. Όλα τα υπόλοιπα FKs είναι υποχρεωτικά (`||`).
- `program_roles.program_id` και `screenings.program_id` έχουν `ON DELETE CASCADE` — η διαγραφή ενός `PROGRAMS` διαγράφει αυτόματα τους σχετικούς ρόλους και προβολές του.
- Ευρετήρια (`ix_program_roles_program`, `ix_program_roles_user`, `ix_screenings_program`, `ix_screenings_submitter`, `ix_screenings_start_time`) υποστηρίζουν τα φίλτρα αναζήτησης των `06`/`09`/`10` και παραλείπονται εδώ ως μη-δομικά στοιχεία του μοντέλου δεδομένων.
