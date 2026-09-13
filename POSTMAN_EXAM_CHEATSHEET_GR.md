# Postman — Σκονάκι Εξέτασης Cinema API

## 1. Πριν ξεκινήσω

Στο PowerShell, μέσα στον φάκελο του project:

```powershell
.\venv\Scripts\Activate.ps1
python init_db.py --seed-demo
python run.py
```

Το API τρέχει στο:

```text
http://127.0.0.1:5000
```

Στο Postman χρησιμοποιώ:

- **Authorization:** `No Auth`
- **Body:** `raw` → `JSON`
- **Header:** `Content-Type: application/json`
- Δεν χρειάζομαι Environment.
- Το Postman κρατά αυτόματα το session cookie μετά το login.
- Όταν κάνω νέο login, αλλάζει ο ενεργός χρήστης.

Demo λογαριασμοί:

| Username | Password | Χρήση |
|---|---|---|
| `programmer` | `Demo123!` | Δημιουργία και διαχείριση προγράμματος |
| `programmer2` | `Demo123!` | Δεύτερος πιθανός programmer |
| `staff` | `Demo123!` | Αξιολόγηση προβολής |
| `submitter` | `Demo123!` | Δημιουργία και υποβολή προβολής |

> Οι ρόλοι PROGRAMMER και STAFF αφορούν συγκεκριμένο πρόγραμμα. Ένας χρήστης
> γίνεται PROGRAMMER όταν δημιουργήσει πρόγραμμα ή προστεθεί σε αυτό, και STAFF
> όταν ένας PROGRAMMER τον προσθέσει στο πρόγραμμα.

---

## 2. Τα βασικά που πρέπει να ξέρω

Ένα HTTP request αποτελείται από:

- **Method:** τι θέλω να κάνω (`GET`, `POST`, `PUT`, `DELETE`).
- **URL:** σε ποιο resource απευθύνομαι.
- **Headers:** πληροφορίες για το request, π.χ. ότι το body είναι JSON.
- **Body:** τα δεδομένα που στέλνω σε `POST` ή `PUT`.
- **Response status:** αν πέτυχε ή γιατί απέτυχε.

Χρήση των methods:

| Method | Σημασία |
|---|---|
| `GET` | Διαβάζω ή αναζητώ δεδομένα |
| `POST` | Δημιουργώ resource ή εκτελώ ενέργεια |
| `PUT` | Ενημερώνω υπάρχον resource |
| `DELETE` | Διαγράφω ή αποσύρω resource |

Σημαντικά status codes:

| Status | Τι σημαίνει |
|---|---|
| `200 OK` | Η ενέργεια πέτυχε |
| `201 Created` | Δημιουργήθηκε νέο resource |
| `204 No Content` | Πέτυχε χωρίς response body |
| `400 Bad Request` | Λάθος ή ελλιπή δεδομένα |
| `401 Unauthorized` | Δεν έχει γίνει login |
| `403 Forbidden` | Έγινε login, αλλά ο χρήστης δεν έχει τον σωστό ρόλο |
| `404 Not Found` | Το resource δεν υπάρχει ή δεν είναι ορατό |
| `409 Conflict` | Η ενέργεια συγκρούεται με την τρέχουσα κατάσταση |

Τα errors επιστρέφονται ως:

```json
{
  "error": "Περιγραφή του προβλήματος"
}
```

---

## 3. Health check

```http
GET http://127.0.0.1:5000/health
```

Αναμενόμενο αποτέλεσμα:

```json
{
  "status": "ok"
}
```

**Εξήγηση:** Ελέγχω ότι ο Flask server λειτουργεί πριν δοκιμάσω το API.

---

## 4. Login και logout

### Login

```http
POST http://127.0.0.1:5000/auth/login
```

```json
{
  "username": "programmer",
  "password": "Demo123!"
}
```

**Εξήγηση:** Το API ελέγχει τα credentials και δημιουργεί session. Το Postman
αποθηκεύει το session cookie, επομένως δεν χρησιμοποιώ Bearer token.

Αναμενόμενο: `200 OK`

```json
{
  "id": "UUID ΤΟΥ ΧΡΗΣΤΗ",
  "username": "programmer",
  "fullName": "Main Programmer"
}
```

### Logout

```http
POST http://127.0.0.1:5000/auth/logout
```

Δεν χρειάζεται body. Αναμενόμενο: `204 No Content`.

---

## 5. Δημιουργία προγράμματος

Πρώτα κάνω login ως `programmer`.

```http
POST http://127.0.0.1:5000/programs
```

```json
{
  "name": "Exam Festival 2027",
  "description": "Program created during the exam",
  "startDate": "2027-06-10",
  "endDate": "2027-06-20"
}
```

Αναμενόμενο: `201 Created`, με `state: "CREATED"`.

**Εξήγηση:** Το endpoint δημιουργεί πρόγραμμα και κάνει αυτόματα τον χρήστη
PROGRAMMER του συγκεκριμένου προγράμματος. Αντιγράφω το `id` από το response και
το χρησιμοποιώ στα επόμενα URLs ως `<PROGRAM_ID>`.

### Προβολή ή αναζήτηση προγραμμάτων

```http
GET http://127.0.0.1:5000/programs
```

```http
GET http://127.0.0.1:5000/programs?name=Exam
```

```http
GET http://127.0.0.1:5000/programs/<PROGRAM_ID>
```

**Εξήγηση:** Τα δεδομένα μετά το `?` είναι query parameters. Περιορίζουν τα
αποτελέσματα χωρίς να αλλάζουν δεδομένα στη βάση.

### Ενημέρωση προγράμματος

```http
PUT http://127.0.0.1:5000/programs/<PROGRAM_ID>
```

```json
{
  "description": "Updated description"
}
```

**Εξήγηση:** Είναι partial update, άρα στέλνω μόνο τα πεδία που αλλάζουν. Μόνο
PROGRAMMER του προγράμματος μπορεί να το κάνει. Ανακοινωμένο πρόγραμμα δεν αλλάζει.

---

## 6. Προσθήκη STAFF

Πρώτα κάνω login ως `staff` και αντιγράφω το `id` του από το response. Μετά κάνω
login ως `programmer` και στέλνω:

```http
POST http://127.0.0.1:5000/programs/<PROGRAM_ID>/roles
```

```json
{
  "userId": "ΤΟ ID ΤΟΥ STAFF",
  "roleType": "STAFF"
}
```

Στη σημερινή τοπική βάση το staff ID είναι:

```text
08c93d44-a96d-44ac-9dfb-c8427c33d441
```

**Εξήγηση:** Ο ρόλος ανατίθεται στον συγκεκριμένο χρήστη μόνο για το συγκεκριμένο
πρόγραμμα. STAFF πρέπει να προστεθεί πριν παγώσει το σύνολο των staff.

---

## 7. Δημιουργία screening

Κάνω login ως `submitter`.

```http
POST http://127.0.0.1:5000/programs/<PROGRAM_ID>/screenings
```

```json
{
  "filmTitle": "Exam Film",
  "filmCast": "Actor One, Actor Two",
  "filmGenres": "Drama, Mystery",
  "filmDurationMinutes": 120,
  "auditoriumName": "Hall A",
  "startTime": "2027-06-12T18:00:00Z"
}
```

Αναμενόμενο: `201 Created`, με `state: "CREATED"`.

**Εξήγηση:** Ο συνδεδεμένος χρήστης γίνεται αυτόματα SUBMITTER/ιδιοκτήτης του
screening. Αντιγράφω το `id` ως `<SCREENING_ID>`.

### Ενημέρωση πριν την υποβολή

```http
PUT http://127.0.0.1:5000/programs/<PROGRAM_ID>/screenings/<SCREENING_ID>
```

```json
{
  "auditoriumName": "Hall B",
  "filmDurationMinutes": 125
}
```

Μόνο ο submitter μπορεί να το αλλάξει και μόνο όσο είναι `CREATED`.

---

## 8. Σειρά καταστάσεων προγράμματος

Η υποχρεωτική σειρά είναι:

```text
CREATED
  → SUBMISSION
  → ASSIGNMENT
  → REVIEW
  → SCHEDULING
  → FINAL_SUBMISSION
  → DECISION
  → ANNOUNCED
```

Η γενική μορφή request είναι:

```http
POST http://127.0.0.1:5000/programs/<PROGRAM_ID>/transitions
```

```json
{
  "targetState": "SUBMISSION"
}
```

Σε κάθε επόμενο βήμα αλλάζω μόνο το `targetState`. Μόνο PROGRAMMER μπορεί να
εκτελεί transitions και δεν επιτρέπεται παράλειψη ή επιστροφή κατάστασης.

---

## 9. Πλήρες screening workflow

### 9.1 Submit

Το πρόγραμμα πρέπει να είναι `SUBMISSION`. Login ως `submitter`:

```http
POST http://127.0.0.1:5000/programs/<PROGRAM_ID>/screenings/<SCREENING_ID>/submit
```

Δεν χρειάζεται body. Το screening γίνεται `SUBMITTED` και το `endTime`
υπολογίζεται από `startTime + filmDurationMinutes`.

### 9.2 Ανάθεση handler

Το πρόγραμμα πρέπει να είναι `ASSIGNMENT`. Login ως `programmer`:

```http
POST http://127.0.0.1:5000/programs/<PROGRAM_ID>/screenings/<SCREENING_ID>/handler
```

```json
{
  "userId": "ΤΟ ID ΤΟΥ STAFF"
}
```

Ο χρήστης πρέπει να είναι ήδη STAFF του ίδιου προγράμματος.

### 9.3 Review

Το πρόγραμμα πρέπει να είναι `REVIEW`. Login ως ο ανατεθειμένος `staff`:

```http
POST http://127.0.0.1:5000/programs/<PROGRAM_ID>/screenings/<SCREENING_ID>/review
```

```json
{
  "score": 8.5,
  "comments": "Strong direction and performances."
}
```

Το screening γίνεται `REVIEWED`.

### 9.4 Approve

Το πρόγραμμα πρέπει να είναι `SCHEDULING`. Login ως `programmer`:

```http
POST http://127.0.0.1:5000/programs/<PROGRAM_ID>/screenings/<SCREENING_ID>/approve
```

```json
{
  "notes": "Approved for the final schedule."
}
```

Το screening γίνεται `APPROVED`.

### 9.5 Final submit

Το πρόγραμμα πρέπει να είναι `FINAL_SUBMISSION`. Login ως `submitter`:

```http
POST http://127.0.0.1:5000/programs/<PROGRAM_ID>/screenings/<SCREENING_ID>/final-submit
```

```json
{
  "auditoriumName": "Hall A",
  "filmTitle": "Exam Film",
  "filmCast": "Actor One, Actor Two",
  "filmGenres": "Drama, Mystery",
  "startTime": "2027-06-12T19:00:00Z"
}
```

Μετά την τελική υποβολή τα στοιχεία παγώνουν.

### 9.6 Accept

Το πρόγραμμα πρέπει να είναι `DECISION`. Login ως `programmer`:

```http
POST http://127.0.0.1:5000/programs/<PROGRAM_ID>/screenings/<SCREENING_ID>/accept
```

Δεν χρειάζεται body. Το screening γίνεται `SCHEDULED`.

### Εναλλακτικά: Reject

```http
POST http://127.0.0.1:5000/programs/<PROGRAM_ID>/screenings/<SCREENING_ID>/reject
```

```json
{
  "reason": "The submission does not meet the requirements."
}
```

Το screening γίνεται `REJECTED`.

---

## 10. Δημόσιο timetable

Αφού το πρόγραμμα γίνει `ANNOUNCED`, κάνω logout και στέλνω:

```http
GET http://127.0.0.1:5000/programs/<PROGRAM_ID>/screenings?view=timetable
```

**Εξήγηση:** Είναι δημόσιο request. Επιστρέφονται μόνο τα δημόσια required πεδία
και κρύβονται εσωτερικά στοιχεία όπως submitter, handler και review comments.

---

## 11. Αρνητικά παραδείγματα που μπορεί να ζητηθούν

### Χωρίς login — αναμένω 401

Κάνω πρώτα logout και μετά:

```http
POST http://127.0.0.1:5000/programs
```

```json
{
  "name": "Unauthorized Program",
  "description": "Should not be created",
  "startDate": "2027-07-01",
  "endDate": "2027-07-10"
}
```

**Γιατί αποτυγχάνει:** Η δημιουργία προγράμματος απαιτεί authenticated user.

### Submitter προσπαθεί να κάνει transition — αναμένω 403

Κάνω login ως `submitter`:

```http
POST http://127.0.0.1:5000/programs/<PROGRAM_ID>/transitions
```

```json
{
  "targetState": "SUBMISSION"
}
```

**Γιατί αποτυγχάνει:** Μόνο PROGRAMMER του προγράμματος επιτρέπεται να αλλάζει
την κατάσταση.

### Λάθος ημερομηνίες — αναμένω 400

```http
POST http://127.0.0.1:5000/programs
```

```json
{
  "name": "Invalid Dates",
  "description": "End date is before start date",
  "startDate": "2027-07-20",
  "endDate": "2027-07-10"
}
```

**Γιατί αποτυγχάνει:** Το `endDate` δεν μπορεί να είναι πριν από το `startDate`.

### Παράλειψη κατάστασης — αναμένω 409

Αν το πρόγραμμα είναι `CREATED`:

```http
POST http://127.0.0.1:5000/programs/<PROGRAM_ID>/transitions
```

```json
{
  "targetState": "REVIEW"
}
```

**Γιατί αποτυγχάνει:** Από `CREATED` επιτρέπεται μόνο μετάβαση σε `SUBMISSION`.

### Ανύπαρκτο resource — αναμένω 404

```http
GET http://127.0.0.1:5000/programs/00000000-0000-0000-0000-000000000000
```

---

## 12. Πιθανές προφορικές ερωτήσεις

### «Γιατί δεν βάζεις Authorization header;»

Η εφαρμογή χρησιμοποιεί session-based authentication. Μετά το login ο server
στέλνει cookie και το Postman το επιστρέφει αυτόματα στα επόμενα requests.

### «Ποια είναι η διαφορά 401 και 403;»

- `401`: δεν γνωρίζουμε ποιος είναι ο χρήστης — δεν έχει κάνει login.
- `403`: γνωρίζουμε τον χρήστη, αλλά δεν έχει δικαίωμα για αυτή την ενέργεια.

### «Γιατί χρησιμοποιούμε 409;»

Το request είναι συντακτικά σωστό, αλλά συγκρούεται με την κατάσταση του
συστήματος, π.χ. προσπάθεια review στη λάθος φάση ή διπλό submit.

### «Γιατί το programId βρίσκεται στο URL;»

Επειδή προσδιορίζει το resource στο οποίο απευθύνεται το request. Τα δεδομένα που
περιγράφουν την ενέργεια μπαίνουν στο JSON body.

### «Τι είναι το redaction;»

Το API επιστρέφει διαφορετικά πεδία ανάλογα με τον ρόλο. Ο visitor βλέπει μόνο
δημόσια στοιχεία, ενώ programmer, submitter ή handler μπορούν να δουν τα
εσωτερικά στοιχεία που σχετίζονται με τον ρόλο τους.

### «Πώς ξέρεις ότι ένα request πέτυχε;»

Ελέγχω πρώτα το HTTP status code και μετά το JSON response, ειδικά τα `id`,
`state` και τυχόν `error`.

---

## 13. Γρήγορη σειρά για live επίδειξη

```text
1. GET /health
2. Login programmer
3. POST /programs → αντιγράφω PROGRAM_ID
4. POST /programs/{id}/roles → προσθέτω STAFF
5. Login submitter
6. POST /programs/{id}/screenings → αντιγράφω SCREENING_ID
7. Login programmer → transition SUBMISSION
8. Login submitter → submit screening
9. Login programmer → ASSIGNMENT → assign handler → REVIEW
10. Login staff → review
11. Login programmer → SCHEDULING → approve → FINAL_SUBMISSION
12. Login submitter → final-submit
13. Login programmer → DECISION → accept → ANNOUNCED
14. Logout → δημόσιο GET timetable
```

Αν κάτι αποτύχει, ελέγχω με αυτή τη σειρά:

1. Τρέχει ο server;
2. Έκανα login με τον σωστό χρήστη;
3. Αντέγραψα σωστά τα IDs χωρίς `<` και `>`;
4. Έβαλα `Body → raw → JSON`;
5. Είναι σωστή η τρέχουσα κατάσταση του προγράμματος;
6. Τι γράφει το πεδίο `error` στο response;
