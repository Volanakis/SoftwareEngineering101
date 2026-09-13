# Test Plan & Coverage — Cinema Management Backend

Τεκμηρίωση της σουίτας δοκιμών (Τρίτο Μέρος Εργασίας) για την αναφορά: τι
καλύπτεται, με ποια test cases, υπό ποιες προϋποθέσεις, και πώς εκτελείται.

- **Framework**: `pytest` (το Python-ισοδύναμο του JUnit που προτείνει το εκφώνημα).
- **Σύνολο**: `pytest --collect-only -q` → **183 tests**, 16 αρχεία. Όλα πράσινα.
- **Χρόνος εκτέλεσης**: ~50s (SQLite in-memory).

## Πώς εκτελείται

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pytest                     # όλη η σουίτα
pytest tests/test_program_service.py -q      # ένα module
pytest -k rate_limiting -q                   # ένα θέμα
```

## Κοινές προϋποθέσεις (fixtures — `tests/conftest.py`)

| Fixture | Scope | Τι παρέχει / preconditions |
|---|---|---|
| `app` | function | Flask app με `TestingConfig` (SQLite `:memory:`, `TESTING=True`, rate limiting ενεργό). |
| `client` | function | `app.test_client()` — HTTP-level κλήσεις. |
| `db` | function | `create_all()` πριν το test, `session.remove()` + `drop_all()` μετά. Κάθε test ξεκινά με **άδεια βάση**. |
| `user_factory` | function | `make_user(username=None, password="password123", full_name=...)` — δημιουργεί & αποθηκεύει `User` με hashed password. |
| `_reset_rate_limiter` | function, **autouse** | `limiter.reset()` πριν από κάθε test ώστε το process-global budget του Flask-Limiter να μη διαρρέει μεταξύ tests (ΜΛΑ-3.3). |

Τα περισσότερα HTTP tests προετοιμάζουν γρήγορα το session με
`client.session_transaction()`. Τα πραγματικά `/auth/login` και `/auth/logout`
endpoints ελέγχονται ξεχωριστά στο `test_final_fixes.py`.

## Κάλυψη ανά απαίτηση

| Απαίτηση | Πού καλύπτεται |
|---|---|
| ΛΑ-1.2 authenticate username/password | `test_auth.py` |
| ΛΑ-1.3/1.4 VISITOR/USER fallback ρόλοι | `test_auth.py` (`requires_role` χωρίς `role_getter`) |
| ΛΑ-1.7 PROGRAMMER δεν υποβάλλει στο δικό του πρόγραμμα | `test_screening_service.py`, `test_screenings_blueprint.py` |
| ΛΑ-1.8 έλεγχος εξουσιοδότησης ανά ενέργεια | `test_program_service.py`, `test_screening_service.py` (unauthorised paths) |
| ΛΑ-2.1 create program (unique name, auto id/date, creator→PROGRAMMER) | `test_program_service.py`, `test_programs_blueprint.py`, `test_program_model.py` |
| ΛΑ-2.2 update program (PROGRAMMER, όχι ANNOUNCED, creator διατηρείται) | `test_program_service.py`, `test_programs_blueprint.py` |
| ΛΑ-2.3 / ΛΑ-2.4 add PROGRAMMER / add STAFF (+ πάγωμα STAFF) | `test_program_service.py`, `test_programs_blueprint.py` |
| ΛΑ-2.5 search programs (AND, redaction, sort date→name) | `test_program_service.py`, `test_programs_blueprint.py` |
| ΛΑ-2.6 view program με redaction ανά ρόλο | `test_program_service.py`, `test_programs_blueprint.py` |
| ΛΑ-2.7 delete program (μόνο CREATED) | `test_program_service.py`, `test_programs_blueprint.py` |
| ΛΑ-2.8 state machine (7 μεταβάσεις, no rollback/skip) | `test_program_service.py`, `test_programs_blueprint.py` |
| ΛΑ-2.8.6 auto-reject στο DECISION | `test_screening_decision.py`, `test_integration_lifecycle.py` |
| ΛΑ-3.1/3.2 create / update screening (SUBMITTER, μόνο CREATED) | `test_screening_service.py`, `test_screenings_blueprint.py`, `test_screening_model.py` |
| ΛΑ-3.3/3.4 submit / withdraw | `test_screening_service.py`, `test_screenings_blueprint.py` |
| ΛΑ-3.5 assign handler (ακριβώς ένας STAFF, μόνο ASSIGNMENT) | `test_screening_service.py`, `test_screenings_blueprint.py` |
| ΛΑ-3.6 review (score+comments, μόνο REVIEW) | `test_screening_service.py`, `test_screenings_blueprint.py` |
| ΛΑ-3.7/3.8 approve / reject (manual + automatic, reason υποχρεωτικό) | `test_screening_service.py`, `test_screening_decision.py`, `test_integration_lifecycle.py` |
| ΛΑ-3.9/3.10 final submit / accept (freeze, μόνο DECISION) | `test_screening_service.py`, `test_screenings_blueprint.py` |
| ΛΑ-3.11 search screenings (word-subset AND, sort genre→title / start_time) | `test_screening_service.py`, `test_screenings_blueprint.py` |
| ΛΑ-3.12 view screening με redaction (owner/handler/programmer/visitor) | `test_screening_service.py`, `test_screenings_blueprint.py`, `test_screening_workflow.py` |
| ΜΛΑ-2.1 κατανοητά μηνύματα σφάλματος (όχι 5xx) | error-envelope assertions σε όλα τα `*_blueprint.py` |
| ΜΛΑ-3.1/3.2 authentication + RBAC | `test_auth.py` |
| ΜΛΑ-3.3 rate limiting σε search/submission | `test_rate_limiting.py` |
| ΜΛΑ-4 all-or-nothing (commit μόνο σε πλήρη επιτυχία) | `test_program_service.py`, `test_screening_service.py` (state αμετάβλητο σε σφάλμα) |
| ΜΛΑ-5 audit trail / logging | `test_integration_lifecycle.py` (assertions στα `app.services` log records) |
| Schema / persistence | `test_init_db.py` (SQLAlchemy), `test_sql_schema.py` (`sql/*.sql`) |
| App factory / config | `test_app_factory.py` |

## Περιγραφή ανά αρχείο

| Αρχείο | Επίπεδο | Τι ελέγχει |
|---|---|---|
| `test_app_factory.py` | unit | `create_app` με κάθε config name, blueprints registered, `/health`. |
| `test_auth.py` | unit | `authenticate`, `login_required` (401), `requires_role` (403/allow), VISITOR/USER default. |
| `test_user_model.py` | unit | password hashing, auto UUID, unique username. |
| `test_program_model.py` | unit | defaults (`state=CREATED`, `creation_date`), `programmers`/`staff` properties, unique `name`, cascade. |
| `test_program_service.py` | unit/service | 47 cases — κάθε μέθοδος `ProgramService` + edge cases (διπλό όνομα, μη έγκυρη μετάβαση, μη εξουσιοδοτημένος, redaction tiers). |
| `test_programs_blueprint.py` | HTTP | 25 cases — status codes & JSON σχήματα κάθε `/programs*` endpoint (`API_CONTRACT.md` §3). |
| `test_screening_model.py` | unit | defaults, relationships (`submitter`, `handler`, `program`). |
| `test_screening_service.py` | unit/service | 39 cases — κάθε μέθοδος `ScreeningService`, guards κατάστασης προγράμματος, redaction, search semantics. |
| `test_screenings_blueprint.py` | HTTP | 19 cases — status codes & JSON κάθε `/programs/{pid}/screenings*` endpoint (`API_CONTRACT.md` §4). |
| `test_screening_decision.py` | service | 3 cases — αυτόματη απόρριψη APPROVED-χωρίς-final-submit στο `→ DECISION`, με καταγεγραμμένη αιτιολογία. |
| `test_screening_workflow.py` | HTTP E2E | 1 case — πλήρης happy path CREATED→ANNOUNCED (create→submit→assign→review→approve→final-submit→accept) + visitor redaction. |
| `test_integration_lifecycle.py` | HTTP E2E | 1 case — ένα πρόγραμμα, **τρεις** προβολές σε τρία διαφορετικά τερματικά αποτελέσματα (SCHEDULED / manual REJECTED / auto REJECTED) + έλεγχος audit trail + visitor redaction. |
| `test_rate_limiting.py` | HTTP | 5 cases — 429 μετά το όριο σε `GET /programs`, `GET .../screenings`, `POST .../submit`, `POST .../final-submit`· μη-throttled endpoint δεν περιορίζεται. |
| `test_sql_schema.py` | integration | 4 cases — το `sql/schema.sql` τρέχει σε καθαρή SQLite, columns/nullability ταιριάζουν με τα ORM models, `CHECK` constraints ενεργά, `drop_all.sql` καθαρίζει. |
| `test_final_fixes.py` | regression/HTTP | Authentication endpoints, validation, visibility, nested filters, role separation και κρίσιμοι workflow guards. |
| `test_init_db.py` | integration | Δημιουργία πινάκων, migration του `creator_id` και idempotent demo-user seed. |

## Τι ΔΕΝ καλύπτεται (γνωστά κενά)

- Το rate limiting χρησιμοποιεί in-memory storage· δεν δοκιμάζεται με shared backend (redis).
- Δεν υπάρχει load/performance test για την ΜΛΑ-1 (5–10s ανά αίτημα).
