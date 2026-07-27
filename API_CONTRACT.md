# API Contract — Cinema Management Backend

Συμφωνημένο contract πριν το Person A / Person B διαχωριστούν (Phase 0 του [`TASKS.md`](TASKS.md)). Καλύπτει URL paths, request/response JSON σχήματα και HTTP status codes για κάθε endpoint. Βασίζεται στις απαιτήσεις του [`README.md`](README.md) (`ΛΑ-x.y` / `ΜΛΑ-x`) και στα διαγράμματα του [`diagrams/`](diagrams/) (sequence `11`–`16`, activity `06`–`10`).

Αλλαγές σε αυτό το αρχείο μετά την υλοποίηση απαιτούν συνεννόηση των δύο μελών (evolving contract, όχι frozen spec).

---

## 1. Συμβάσεις

- Όλα τα requests/responses είναι JSON (`Content-Type: application/json`), εκτός `204 No Content`.
- Ημερομηνίες/ώρες σε ISO 8601 (`YYYY-MM-DD` για dates, `YYYY-MM-DDTHH:MM:SSZ` για datetimes).
- Ταυτοποίηση μέσω session cookie (`app.auth.login_user` / `login_required`, βλ. `app/auth.py`) — όχι token-based, εκτός αν αλλάξει το contract.
- **Error envelope** (σταθερό σχήμα σε κάθε μη-2xx response, ΜΛΑ-2.1):
  ```json
  { "error": "human-readable message" }
  ```
- **Status codes** που χρησιμοποιούνται σε όλο το API:
  | Code | Χρήση |
  |---|---|
  | 200 | Επιτυχής GET/POST/PUT που επιστρέφει body |
  | 201 | Επιτυχής δημιουργία πόρου |
  | 204 | Επιτυχής ενέργεια χωρίς response body (delete/withdraw/logout) |
  | 400 | Ελλιπές/μη έγκυρο input (validation) |
  | 401 | Μη αυθεντικοποιημένος χρήστης όπου απαιτείται login |
  | 403 | Αυθεντικοποιημένος αλλά μη εξουσιοδοτημένος (λάθος ρόλος) |
  | 404 | Ο πόρος δεν βρέθηκε |
  | 409 | Conflict: μη έγκυρη state transition, διπλότυπο, παγωμένο σύνολο, κ.λπ. |
- **Ιδεμποτεντικότητα** (ΜΛΑ-2.2): GET είναι πάντα ασφαλές να επαναληφθεί. Ενέργειες δημιουργίας/μετάβασης δεν πρέπει να εκτελούνται διπλά — το unique constraint σε `Program.name` και οι έλεγχοι state το διασφαλίζουν φυσικά· δεν χρειάζεται ξεχωριστό idempotency key σε αυτή τη φάση.
- **Redaction ανά ρόλο** (ΛΑ-2.6, ΛΑ-3.12): κάθε GET endpoint επιστρέφει διαφορετικό υποσύνολο πεδίων ανάλογα με τον ρόλο του requester πάνω στον συγκεκριμένο πόρο. Οι ακριβείς κανόνες redaction ζουν στο service layer (`ProgramService`/`ScreeningService`), το contract εδώ ορίζει μόνο το πλήρες schema και τα δύο tiers (public/full).

---

## 2. Auth

### `POST /auth/login`

Request:
```json
{ "username": "string", "password": "string" }
```

Responses:
- `200 OK` → `{ "id": "uuid", "username": "string", "fullName": "string" }`
- `400` — ελλιπή πεδία
- `401` — λάθος συνδυασμός username/password (ΛΑ-1.2)

### `POST /auth/logout`

Δεν απαιτεί body.

- `204 No Content`

---

## 3. Programs — `/programs`

### DTO schema (`ProgramDTO`)

Πλήρες σχήμα (PROGRAMMER/STAFF του συγκεκριμένου προγράμματος βλέπουν όλα τα πεδία):

```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "startDate": "date",
  "endDate": "date",
  "creationDate": "datetime",
  "state": "CREATED|SUBMISSION|ASSIGNMENT|REVIEW|SCHEDULING|FINAL_SUBMISSION|DECISION|ANNOUNCED",
  "programmers": [{ "id": "uuid", "username": "string", "fullName": "string" }],
  "staff": [{ "id": "uuid", "username": "string", "fullName": "string" }]
}
```

Public tier (VISITOR, ή USER χωρίς ρόλο σε αυτό το πρόγραμμα — ΛΑ-2.6): μόνο `id`, `name`, `description`, `startDate`, `endDate`, `state`. Τα `creationDate`, `programmers`, `staff` αποκρύπτονται.

### `POST /programs`

ΛΑ-2.1, sequence `11`. Απαιτεί authenticated χρήστη (ρόλος USER, ΛΑ-1.4).

Request:
```json
{ "name": "string", "description": "string", "startDate": "date", "endDate": "date" }
```

Responses:
- `201 Created` → `ProgramDTO` (πλήρες, ο caller είναι πλέον PROGRAMMER)
- `400` — λείπει υποχρεωτικό πεδίο
- `401` — μη αυθεντικοποιημένος
- `409` — `name` ήδη σε χρήση

### `GET /programs`

ΛΑ-2.5, activity `09`. Ανοιχτό σε VISITOR.

Query params (όλα προαιρετικά, συνδυάζονται με AND): `name`, `description`, `startDateFrom`, `startDateTo`, `endDateFrom`, `endDateTo`, `filmTitle`, `auditorium` (τα δύο τελευταία φιλτράρουν βάσει screenings του προγράμματος).

Responses:
- `200 OK` → `{ "results": [ProgramDTO, ...] }` — redacted ανά ρόλο, χωρίς κριτήρια επιστρέφονται όλα, ταξινόμηση `startDate` → `name`.

### `GET /programs/{id}`

ΛΑ-2.6, sequence `14`. Ανοιχτό σε VISITOR.

Responses:
- `200 OK` → `ProgramDTO` (redacted ανά ρόλο του requester)
- `404` — δεν υπάρχει πρόγραμμα με αυτό το id

### `PUT /programs/{id}`

ΛΑ-2.2, sequence `13`. Μόνο PROGRAMMER του προγράμματος.

Request (όλα προαιρετικά, partial update):
```json
{ "name": "string", "description": "string", "startDate": "date", "endDate": "date" }
```

Responses:
- `200 OK` → `ProgramDTO`
- `400` — μη έγκυρο input (π.χ. `endDate < startDate`)
- `403` — requester δεν είναι PROGRAMMER αυτού του προγράμματος
- `404` — δεν υπάρχει
- `409` — `state == ANNOUNCED` (ΛΑ-2.2.4) ή `name` conflict με άλλο πρόγραμμα

### `DELETE /programs/{id}`

ΛΑ-2.7, sequence `15`. Μόνο PROGRAMMER, μόνο `state == CREATED`.

Responses:
- `204 No Content`
- `403` — δεν είναι PROGRAMMER
- `404` — δεν υπάρχει
- `409` — `state != CREATED`

### `POST /programs/{id}/roles`

ΛΑ-2.3 / ΛΑ-2.4, sequence `12`. Μόνο PROGRAMMER του προγράμματος.

Request:
```json
{ "userId": "uuid", "roleType": "PROGRAMMER|STAFF" }
```

Responses:
- `200 OK` → `ProgramDTO` (ενημερωμένο)
- `400` — άγνωστο `roleType` ή λείπει `userId`
- `403` — requester δεν είναι PROGRAMMER
- `404` — πρόγραμμα ή user δεν υπάρχει
- `409` — ο χρήστης είναι ήδη PROGRAMMER (ΛΑ-2.3), ή `roleType == STAFF` αλλά `state` έχει προσπεράσει `SUBMISSION` — παγωμένο σύνολο (ΛΑ-2.4)

### `DELETE /programs/{id}/roles/{userId}`

Αφαίρεση από PROGRAMMERS/STAFF (μέρος του ΛΑ-2.2.2). Μόνο PROGRAMMER.

Responses:
- `204 No Content`
- `403` — requester δεν είναι PROGRAMMER
- `404` — πρόγραμμα, user, ή role assignment δεν υπάρχει
- `409` — προσπάθεια αφαίρεσης του creator (ΛΑ-2.2.3), `state == ANNOUNCED`, ή STAFF set παγωμένο (ΛΑ-2.4)

### `POST /programs/{id}/transitions`

ΛΑ-2.8, activity `06`. Μόνο PROGRAMMER. Καλύπτει και τις 7 μεταβάσεις· η μετάβαση σε `DECISION` πυροδοτεί εσωτερικά (χωρίς ξεχωριστό client call) το auto-reject εγκεκριμένων-αλλά-μη-τελικά-υποβληθέντων screenings (ΛΑ-2.8.6 / activity `08`, S6).

Request:
```json
{ "targetState": "SUBMISSION|ASSIGNMENT|REVIEW|SCHEDULING|FINAL_SUBMISSION|DECISION|ANNOUNCED" }
```

Responses:
- `200 OK` → `ProgramDTO` (νέα κατάσταση)
- `403` — requester δεν είναι PROGRAMMER
- `404` — δεν υπάρχει
- `409` — η μετάβαση δεν είναι η επόμενη επιτρεπτή (χωρίς rollback/skip)

---

## 4. Screenings — `/programs/{pid}/screenings`

Όλα τα endpoints είναι εμφωλευμένα σε ένα πρόγραμμα (`pid`). `404` αν το `pid` δεν υπάρχει, πριν από οποιονδήποτε άλλο έλεγχο.

### DTO schema (`ScreeningDTO`)

Πλήρες σχήμα (SUBMITTER owner, ανατεθειμένος STAFF handler, ή οποιοσδήποτε PROGRAMMER του προγράμματος — ΛΑ-3.12):

```json
{
  "id": "uuid",
  "creationDate": "datetime",
  "state": "CREATED|SUBMITTED|REVIEWED|APPROVED|SCHEDULED|REJECTED",
  "filmTitle": "string",
  "filmCast": "string",
  "filmGenres": "string",
  "filmDurationMinutes": "int",
  "auditoriumName": "string",
  "startTime": "datetime",
  "endTime": "datetime",
  "submitterId": "uuid",
  "handlerId": "uuid|null",
  "reviewScore": "number|null",
  "reviewComments": "string|null",
  "rejectionReason": "string|null"
}
```

Public tier (VISITOR, ή αυθεντικοποιημένος χρήστης χωρίς σχέση με αυτή την προβολή): `id`, `filmTitle`, `filmCast`, `filmGenres`, `auditoriumName`, `startTime`, `endTime`, `state`. Τα `reviewScore`, `reviewComments`, `rejectionReason`, `submitterId`, `handlerId`, `creationDate` αποκρύπτονται.

### `POST /programs/{pid}/screenings`

ΛΑ-3.1, activity `07`. Απαιτεί authenticated χρήστη (USER). Ο caller γίνεται αυτόματα SUBMITTER. Ένας PROGRAMMER αυτού του προγράμματος δεν επιτρέπεται να υποβάλει (ΛΑ-1.7).

Request (μερικά πεδία μπορούν να συμπληρωθούν αργότερα με `PUT`, πριν το submit):
```json
{ "filmTitle": "string", "filmCast": "string", "filmGenres": "string", "filmDurationMinutes": "int", "auditoriumName": "string", "startTime": "datetime" }
```

Responses:
- `201 Created` → `ScreeningDTO` (`state = CREATED`, `endTime = null` μέχρι submit)
- `400` — λείπει `filmTitle`
- `401` — μη αυθεντικοποιημένος
- `403` — ο caller είναι PROGRAMMER αυτού του προγράμματος (ΛΑ-1.7)
- `404` — πρόγραμμα δεν υπάρχει

### `GET /programs/{pid}/screenings`

ΛΑ-3.11, activity `10`. Ανοιχτό σε VISITOR.

Query params (AND, word-subset case-insensitive σε text πεδία): `filmTitle`, `cast`, `genre`, `dateFrom`, `dateTo`, `view=timetable` (προαιρετικό flag).

Responses:
- `200 OK` → `{ "results": [ScreeningDTO, ...] }` — redacted ανά ρόλο· ταξινόμηση κατά `genre` → `filmTitle`, ή κατά `startTime` αν `view=timetable`.
- `404` — πρόγραμμα δεν υπάρχει

### `GET /programs/{pid}/screenings/{id}`

ΛΑ-3.12, sequence `16`. Ανοιχτό σε VISITOR.

Responses:
- `200 OK` → `ScreeningDTO` (redacted)
- `404` — πρόγραμμα ή screening δεν υπάρχει

### `PUT /programs/{pid}/screenings/{id}`

ΛΑ-3.2. Μόνο SUBMITTER, μόνο `state == CREATED`.

Request (partial update, όλα προαιρετικά): `{ "auditoriumName": "string", "filmTitle": "string", "filmCast": "string", "filmGenres": "string", "filmDurationMinutes": "int", "startTime": "datetime" }`

Responses:
- `200 OK` → `ScreeningDTO`
- `400` — μη έγκυρο input
- `403` — requester δεν είναι ο SUBMITTER
- `404` — δεν υπάρχει
- `409` — `state != CREATED`

### `POST /programs/{pid}/screenings/{id}/submit`

ΛΑ-3.3, `CREATED → SUBMITTED`. Μόνο SUBMITTER. Απαιτεί `program.state == SUBMISSION` και πλήρη screening (`filmTitle`, `auditoriumName`, `filmDurationMinutes`, `startTime`). Το `endTime` υπολογίζεται αυτόματα (`startTime + filmDurationMinutes`).

Responses:
- `200 OK` → `ScreeningDTO`
- `403` — requester δεν είναι ο SUBMITTER
- `404` — δεν υπάρχει
- `409` — `program.state != SUBMISSION`, ή screening ελλιπές, ή `screening.state != CREATED`

### `DELETE /programs/{pid}/screenings/{id}` (withdraw)

ΛΑ-3.4. Μόνο SUBMITTER, μόνο `state == CREATED`. Οριστική διαγραφή.

Responses:
- `204 No Content`
- `403` — requester δεν είναι ο SUBMITTER
- `404` — δεν υπάρχει
- `409` — `state != CREATED`

### `POST /programs/{pid}/screenings/{id}/handler`

ΛΑ-3.5, activity `08` (S1). Μόνο PROGRAMMER, μόνο `program.state == ASSIGNMENT`.

Request: `{ "userId": "uuid" }` (πρέπει να είναι STAFF του προγράμματος)

Responses:
- `200 OK` → `ScreeningDTO` (`handlerId` ορισμένο)
- `403` — requester δεν είναι PROGRAMMER
- `404` — δεν υπάρχει, ή `userId` δεν είναι STAFF αυτού του προγράμματος
- `409` — `program.state != ASSIGNMENT`, ή υπάρχει ήδη handler

### `POST /programs/{pid}/screenings/{id}/review`

ΛΑ-3.6, `→ REVIEWED`. Μόνο ο ανατεθειμένος STAFF handler, μόνο `program.state == REVIEW`.

Request: `{ "score": "number", "comments": "string" }`

Responses:
- `200 OK` → `ScreeningDTO`
- `400` — λείπει `score`/`comments`
- `403` — requester δεν είναι ο handler
- `404` — δεν υπάρχει
- `409` — `program.state != REVIEW`

### `POST /programs/{pid}/screenings/{id}/approve`

ΛΑ-3.7, `→ APPROVED`. Μόνο PROGRAMMER, μόνο `program.state == SCHEDULING`.

Request: `{ "notes": "string" }` (προαιρετικό — σημειώσεις για ζητούμενες αλλαγές πριν το final submission)

Responses:
- `200 OK` → `ScreeningDTO`
- `403` — requester δεν είναι PROGRAMMER
- `404` — δεν υπάρχει
- `409` — `program.state != SCHEDULING`, ή `screening.state != REVIEWED`

### `POST /programs/{pid}/screenings/{id}/reject`

ΛΑ-3.8 (χειροκίνητη μόνο — η αυτόματη απόρριψη ΛΑ-3.8.2 δεν έχει δικό της client endpoint, εκτελείται εσωτερικά από `POST /programs/{id}/transitions` όταν `targetState == DECISION`). `→ REJECTED` (τελική). Μόνο PROGRAMMER· επιτρέπεται όταν `program.state == SCHEDULING` (βάσει review) ή `program.state == DECISION` (final submission δεν κάλυψε τις απαιτούμενες αλλαγές).

Request: `{ "reason": "string" }` (υποχρεωτικό — ΛΑ-3.8.3)

Responses:
- `200 OK` → `ScreeningDTO`
- `400` — λείπει `reason`
- `403` — requester δεν είναι PROGRAMMER
- `404` — δεν υπάρχει
- `409` — `program.state` εκτός `{SCHEDULING, DECISION}`, ή screening ήδη σε τελική κατάσταση

### `POST /programs/{pid}/screenings/{id}/final-submit`

ΛΑ-3.9. Μόνο SUBMITTER, μόνο `program.state == FINAL_SUBMISSION` και `screening.state == APPROVED`. Μετά την επιτυχή εκτέλεση τα στοιχεία παγώνουν.

Request (τελικό bundle αλλαγών, όλα προαιρετικά): `{ "auditoriumName": "string", "filmTitle": "string", "filmCast": "string", "filmGenres": "string", "startTime": "datetime" }`

Responses:
- `200 OK` → `ScreeningDTO` (frozen)
- `403` — requester δεν είναι ο SUBMITTER
- `404` — δεν υπάρχει
- `409` — `program.state != FINAL_SUBMISSION`, ή `screening.state != APPROVED`

### `POST /programs/{pid}/screenings/{id}/accept`

ΛΑ-3.10, `→ SCHEDULED` (τελική). Μόνο PROGRAMMER, μόνο `program.state == DECISION`, μόνο για screening που είναι `APPROVED` **και** έχει γίνει final submission.

Responses:
- `200 OK` → `ScreeningDTO`
- `403` — requester δεν είναι PROGRAMMER
- `404` — δεν υπάρχει
- `409` — `program.state != DECISION`, ή screening δεν πληροί τις προϋποθέσεις (μη εγκεκριμένο ή μη τελικά υποβληθέν — στην περίπτωση αυτή θα έχει ήδη αυτόματα απορριφθεί από τη μετάβαση σε `DECISION`)

---

## 5. Κάλυψη use cases

Κάθε endpoint παραπάνω αντιστοιχεί 1-1 σε ΛΑ requirement / diagram, ώστε η υλοποίηση (Person A: §3, Person B: §4) να μην χρειάζεται νέα endpoints χωρίς ενημέρωση αυτού του αρχείου. Rate limiting (ΜΛΑ-3.3, cross-cutting task) εφαρμόζεται πάνω σε submission (`POST .../submit`, `.../final-submit`) και search (`GET /programs`, `GET .../screenings`) endpoints χωρίς να αλλάζει το request/response schema τους.
