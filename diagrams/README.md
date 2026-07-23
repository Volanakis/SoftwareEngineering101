# Διαγράμματα Σχεδίασης – Cinema Management Backend System

Αυτός ο φάκελος περιέχει το πλήρες σύνολο διαγραμμάτων σχεδίασης (UML) που ζητούνται στο **Δεύτερο Μέρος** της εργασίας (321-4002 – Software Engineering, 30/100), σε μορφή `.excalidraw` (ανοίγουν απευθείας στο [excalidraw.com](https://excalidraw.com) ή στο VS Code plugin Excalidraw). Κάθε αρχείο είναι αυτόνομο και επεξεργάσιμο.

Ο σχεδιασμός βασίζεται στην ανάλυση απαιτήσεων του εγγράφου `ΕΡΓΑΣΙΑ ΜΑΘΗΜΑΤΟΣ 2025 - ΟΜΑΔΕΣ ΕΝΟΣ Ή ΔΥΟ ΑΤΟΜΩΝ.pdf`. Παρακάτω περιγράφεται αναλυτικά ο σκοπός, το περιεχόμενο και η αιτιολόγηση κάθε διαγράμματος.

---

## 0. Παραδοχές που επιλύουν ασάφειες του εκφωνήματος

Η εργασία επιτρέπει ρητά την τεκμηρίωση παραδοχών όπου η εκφώνηση είναι ασαφής ή αντιφατική. Οι παρακάτω παραδοχές έγιναν **πριν** τη σχεδίαση και αντικατοπτρίζονται σε όλα τα διαγράμματα:

1. **Ονοματολογία καταστάσεων προγράμματος**: Στην ενότητα «FUNCTIONS/REQUIREMENTS» χρησιμοποιείται η κατάσταση `FINAL_PUBLICATION`, ενώ στην ενότητα «ENTITIES» χρησιμοποιείται `FINAL_SUBMISSION`. Θεωρούμε ότι πρόκειται για την **ίδια** κατάσταση και υιοθετούμε ενιαία το όνομα **`FINAL_SUBMISSION`** (όπως στην περιγραφή της οντότητας Program), αφού είναι πιο περιγραφικό της λειτουργίας (οι submitters υποβάλλουν τελικές εκδόσεις).
2. **Ποιος εγκρίνει/απορρίπτει μία προβολή (Screening approval/rejection)**: Στην περιγραφή της λειτουργίας «Screening approval» (σελ. 3) αναφέρεται ότι επιτρέπεται *«by a SUBMITTER»*, κάτι που έρχεται σε **άμεση αντίφαση** με τον πίνακα ρόλων (σελ. 5), όπου η «screening approval/rejection/acceptance» ανήκει ρητά στις αρμοδιότητες του **PROGRAMMER**, καθώς και με τη γενικότερη αρχή αμεροληψίας του εγγράφου («a PROGRAMMER should not submit screenings in his/her own program»). Θα ήταν λογικά ασυνεπές ένας SUBMITTER να εγκρίνει τη δική του υποβολή. Επιλύουμε την αντίφαση υπέρ του πίνακα ρόλων: **η έγκριση και η χειροκίνητη απόρριψη προβολών εκτελούνται από PROGRAMMER**, όχι από SUBMITTER. Αυτό αποτυπώνεται σε όλα τα σχετικά διαγράμματα (use case, activity, class).
3. **«Create Program» / «Create Screening» ως use case του USER**: Παρότι ο δημιουργός αποκτά αμέσως τον ρόλο PROGRAMMER (ή SUBMITTER), το ενεργοποιούν actor είναι ο USER (καθώς αυτό είναι το μόνο προαπαιτούμενο), σύμφωνα με τον πίνακα ρόλων. Ο νέος ρόλος είναι το **αποτέλεσμα**, όχι η προϋπόθεση, της ενέργειας.
4. **Ρόλος SUBMITTER δεν αποθηκεύεται ως ProgramRole**: Το SUBMITTER δεν είναι εγγεγραμμένος ρόλος στο σύνολο PROGRAMMERS/STAFF ενός Program· προκύπτει έμμεσα από τη σχέση `Screening.submitter`. Αυτό αποτυπώνεται στο class diagram.

---

## 1. Σύνοψη διαγραμμάτων & Κάλυψη Use Cases

Η εργασία απαιτεί ένα σύνολο activity diagrams και ένα σύνολο sequence diagrams που **από κοινού** να καλύπτουν όλα τα μοντελοποιημένα use cases, **χωρίς** κανένα use case να καλύπτεται και από τα δύο (καμία επικάλυψη ζεύγους activity/sequence πάνω στο ίδιο use case). Ακολουθεί ο πλήρης χάρτης κάλυψης (20 use cases συνολικά):

| # | Use Case | Καλύπτεται από |
|---|----------|-----------------|
| 1 | Program Creation | Sequence #11 |
| 2 | Program Update | Sequence #13 |
| 3 | Add Programmer | Sequence #12 |
| 4 | Add Staff | Sequence #12 |
| 5 | Program Search | Activity #09 |
| 6 | Program View | Sequence #14 |
| 7 | Program Deletion | Sequence #15 |
| 8 | Program State Update (7 μεταβάσεις) | Activity #06 |
| 9 | Screening Creation | Activity #07 |
| 10 | Screening Update | Activity #07 |
| 11 | Screening Submission | Activity #07 |
| 12 | Screening Withdrawal | Activity #07 |
| 13 | Assign Handler (STAFF) | Activity #08 |
| 14 | Screening Review | Activity #08 |
| 15 | Screening Approval | Activity #08 |
| 16 | Screening Rejection (manual & automatic) | Activity #08 |
| 17 | Screening Final Submission | Activity #08 |
| 18 | Screening Acceptance (Scheduling) | Activity #08 |
| 19 | Screening Search | Activity #10 |
| 20 | Screening View | Sequence #16 |

**Σκεπτικό ομαδοποίησης**: Τα use cases που αποτελούν στάδια ενός **ενιαίου, αλληλένδετου κύκλου ζωής με πολλαπλές αποφάσεις/διακλαδώσεις** (μεταβάσεις κατάστασης προγράμματος, ροή υποβολής προβολής, ροή αξιολόγησης→απόφασης, αναζητήσεις με φιλτράρισμα) μοντελοποιούνται καλύτερα ως **activity diagrams**, όπου φαίνονται καθαρά οι συνθήκες (guards) και οι εναλλακτικές διαδρομές. Τα use cases που είναι κυρίως **αλληλεπιδράσεις request/response μεταξύ στρώσεων συστήματος** (CRUD-like: δημιουργία, ενημέρωση, προβολή, διαγραφή, ανάθεση ρόλων) μοντελοποιούνται καλύτερα ως **sequence diagrams**, όπου φαίνεται καθαρά η ροή κλήσεων μεταξύ REST Resource → Service → Repository → Database.

### Πλήρης λίστα αρχείων

Κάθε διάγραμμα υπάρχει σε **δύο μορφές**: το επεξεργάσιμο `.excalidraw` (για το excalidraw.com / VS Code extension) και ένα αντίστοιχο **`.md` με ενσωματωμένο Mermaid diagram**, ίδιου ονόματος, που αποδίδεται αυτόματα ως εικόνα μέσα στο GitHub, στο GitLab και στο preview του VS Code — χωρίς να χρειάζεται άνοιγμα του excalidraw. Όλα τα `.md` αρχεία έχουν επαληθευτεί ότι κάνουν parse/render σωστά με το `@mermaid-js/mermaid-cli`.

| Αρχείο (.excalidraw / .md) | Τύπος | Τίτλος |
|---|---|---|
| `01-context-diagram` | Context | Πλαίσιο συστήματος |
| `02-usecase-program-management` | Use Case | Διαχείριση Προγράμματος |
| `03-usecase-screening-management` | Use Case | Διαχείριση Προβολών |
| `04-component-diagram` | Component | Αρχιτεκτονική συστήματος |
| `05-class-diagram` | Class | Οντότητες δεδομένων |
| `06-activity-program-state-transitions` | Activity | Μεταβάσεις κατάστασης προγράμματος |
| `07-activity-screening-submission` | Activity | Ροή υποβολής προβολής |
| `08-activity-screening-review-decision` | Activity | Ροή αξιολόγησης → απόφασης προβολής |
| `09-activity-program-search` | Activity | Αναζήτηση προγραμμάτων |
| `10-activity-screening-search` | Activity | Αναζήτηση προβολών |
| `11-sequence-program-creation` | Sequence | Δημιουργία προγράμματος |
| `12-sequence-add-programmer-staff` | Sequence | Προσθήκη PROGRAMMER/STAFF |
| `13-sequence-program-update` | Sequence | Ενημέρωση προγράμματος |
| `14-sequence-program-view` | Sequence | Προβολή προγράμματος (redaction) |
| `15-sequence-program-deletion` | Sequence | Διαγραφή προγράμματος |
| `16-sequence-screening-view` | Sequence | Προβολή προβολής (redaction) |

**Σημείωση για τα Mermaid `.md`**: το Mermaid δεν διαθέτει native τύπο για use case ή component diagrams, οπότε τα `02`, `03`, `04` αποδίδονται ως `flowchart` (actors/use cases ως κόμβοι, boundary ως subgraph) — σημασιολογικά ταυτόσημα με το `.excalidraw`, με αυτόματο (διαφορετικό) layout. Τα `05` (class), και `11`–`16` (sequence) χρησιμοποιούν τους αντίστοιχους **native** τύπους του Mermaid (`classDiagram`, `sequenceDiagram` με πραγματικά `alt` fragments), ενώ τα activity diagrams `06`–`10` αποδίδονται ως `flowchart` με `subgraph` για τα διαδικά (swimlanes).

---

## 2. Αρχιτεκτονική & Πλαίσιο Συστήματος

### 2.1 Context Diagram — `01-context-diagram.excalidraw`

Απεικονίζει το **Cinema Management Backend System** ως «μαύρο κουτί» και το περιβάλλον του:

- **Visitor** (μη αυθεντικοποιημένος χρήστης): αναζητά/βλέπει μόνο ANNOUNCED προγράμματα και SCHEDULED προβολές.
- **Registered User** (συγκεντρωτικά User/Programmer/Staff/Submitter, αφού οι συγκεκριμένοι ρόλοι είναι δυναμικοί ανά πρόγραμμα): αυθεντικοποιείται και εκτελεί διαχειριστικές ενέργειες ανάλογα με τον ρόλο του.
- **User Management System** (εξωτερικό, στικτό πλαίσιο): σύστημα διαχείρισης χρηστών που, σύμφωνα με την παραδοχή του εκφωνήματος, μοιράζεται την ίδια σχεσιακή βάση δεδομένων (πίνακας Users) με το cinema backend· η αυθεντικοποίηση/εξουσιοδότηση όμως υλοποιείται **μέσα** στο cinema backend.
- **Cinema Relational Database** (εξωτερικό ως προς τη λογική του backend, αλλά μέρος της υποδομής): αποθηκεύει Programs, Screenings, Users, ProgramRoles με απαίτηση συναλλακτικότητας (transactionality).

Το διάγραμμα δικαιολογεί γιατί το σύστημα χρειάζεται authentication/authorization module εσωτερικά (η ασάφεια/παραδοχή #7 του εγγράφου) και γιατί η βάση είναι διαμοιραζόμενη.

### 2.2 Component Diagram — `04-component-diagram.excalidraw`

Παρουσιάζει μια τυπική **layered / RESTful αρχιτεκτονική**:

1. **Client Applications**: οποιοσδήποτε HTTP client (browser, Postman, front-end εφαρμογή).
2. **Presentation layer**: `Program REST Resource` και `Screening REST Resource`, υλοποιημένα ως **Flask Blueprints** (Python), υπεύθυνα για (de)serialization (JSON) και HTTP status codes.
3. **Cross-cutting concerns**: `Authentication & Authorization Filter` (υλοποιείται ως Flask `before_request` hook που ελέγχει credentials & ρόλους πριν φτάσει το αίτημα στο blueprint) και `Rate Limiter` (**Flask-Limiter**, προστασία από κατάχρηση σε ενέργειες όπως υποβολές προβολών/αναζητήσεις — μη λειτουργική απαίτηση του εκφωνήματος).
4. **Service layer**: `Program Service` και `Screening Service`, όπου βρίσκεται όλη η επιχειρησιακή λογική (state machine κανόνες, redaction ανά ρόλο, λογική αναζήτησης). Το `Screening Service` εξαρτάται από το `Program Service` για να διαβάζει την τρέχουσα κατάσταση του προγράμματος (π.χ. για να επιτρέψει υποβολή μόνο όταν state=SUBMISSION).
5. **Logging & Audit Component**: κεντρική καταγραφή σφαλμάτων και ιστορικού ενεργειών (audit trail), απαίτηση αξιοπιστίας του εκφωνήματος.
6. **Data Access layer**: `Program Repository`, `Screening Repository`, `User Repository`, υλοποιημένα ως **SQLAlchemy** models/queries πάνω από τη βάση.
7. **Cinema Relational Database** & **External User Management System**.

**Τεχνολογική στοίβα (υλοποίηση σε Python)**: Flask (RESTful services), SQLAlchemy (ORM), Flask-Limiter (rate limiting), pytest (unit testing) — τα αντίστοιχα εργαλεία Python για Maven/JUnit/Jersey που αναφέρει το εκφώνημα ως εναλλακτική στην περίπτωση μη χρήσης Java.

Το βέλος `User Repository → External User Management System` αντιπροσωπεύει τον συγχρονισμό/επαλήθευση με το εξωτερικό σύστημα διαχείρισης χρηστών.

---

## 3. Use Cases

### 3.1 `02-usecase-program-management.excalidraw`

Actors: **Visitor**, **User** (γενίκευση του Visitor), **Programmer** (γενίκευση του User). Use cases: Search Programs, View Program, Create Program, Update Program, Add Programmer, Add Staff, Delete Program, Update Program State (ένα ενιαίο use case που αντιπροσωπεύει και τις 7 επιτρεπτές μεταβάσεις καταστάσεων, βλ. §4.1). Ο Visitor συνδέεται μόνο με Search/View (καθώς αυτά είναι κοινά, με redaction στο περιεχόμενο ανάλογα με τον ρόλο)· ο User προσθέτει το Create Program· ο Programmer προσθέτει όλες τις διαχειριστικές ενέργειες.

### 3.2 `03-usecase-screening-management.excalidraw`

Actors: **Visitor**, **User**, **Submitter**, **Staff**, **Programmer** (οι τρεις τελευταίοι είναι γενικεύσεις του User — υπενθυμίζεται ότι ένας χρήστης μπορεί να έχει διαφορετικό ρόλο σε διαφορετικό πρόγραμμα, αλλά το διάγραμμα δείχνει τις δυνατότητες ανά ρόλο, ανεξαρτήτως προγράμματος). 12 use cases: Search/View Screening (κοινά, redaction ανά ρόλο), Create Screening (User), Update/Submit/Withdraw/Final Submission Screening (Submitter — μόνο για τις δικές του προβολές), Review Screening (Staff — μόνο για προβολές όπου έχει οριστεί handler), Assign Handler/Approve/Reject/Accept Screening (Programmer — σύμφωνα με την παραδοχή §0.2).

---

## 4. Συμπεριφορά Συστήματος

### 4.1 Activity — Μεταβάσεις Κατάστασης Προγράμματος (`06-activity-program-state-transitions.excalidraw`)

Καλύπτει το use case **Program State Update** συνολικά (και τις 7 επιτρεπτές μεταβάσεις: CREATED→SUBMISSION→ASSIGNMENT→REVIEW→SCHEDULING→FINAL_SUBMISSION→DECISION→ANNOUNCED), αντί να σχεδιαστούν 7 ξεχωριστά διαγράμματα, αφού μοιράζονται πανομοιότυπη δομή ελέγχου. Δύο διαδικά (swimlanes): **Programmer** και **System**. Ροή:

1. Ο Programmer επιλέγει την επόμενη κατάσταση-στόχο και υποβάλλει αίτημα μετάβασης.
2. Το σύστημα ελέγχει ότι ο αιτών ανήκει στο σύνολο PROGRAMMERS του προγράμματος (αλλιώς 403 Unauthorized).
3. Το σύστημα ελέγχει ότι η ζητούμενη μετάβαση είναι η **επόμενη στη σταθερή ακολουθία** (καμία επιστροφή πίσω/rollback, καμία παράλειψη βήματος — αλλιώς 409 Invalid transition).
4. Εφαρμόζονται πλευρικές ενέργειες ειδικές για τη μετάβαση (π.χ. άνοιγμα/κλείσιμο υποβολών, πάγωμα συνόλου STAFF, ενεργοποίηση reviews).
5. **Ειδική περίπτωση**: αν ο στόχος είναι DECISION, οι εγκεκριμένες (APPROVED) προβολές που δεν έχουν κάνει final submission απορρίπτονται αυτόματα.
6. Η νέα κατάσταση αποθηκεύεται (persist) μαζί με εγγραφή audit log και επιστρέφεται 200 OK.

### 4.2 Activity — Ροή Υποβολής Προβολής (`07-activity-screening-submission.excalidraw`)

Καλύπτει τα use cases **Screening Creation, Update, Submission, Withdrawal**. Δύο διαδικά: **Submitter (owner)** και **System**.

1. Δημιουργία screening (επιλογή προγράμματος + αρχικά πεδία) → το σύστημα αυτόματα αναθέτει τον ρόλο SUBMITTER στον δημιουργό, παράγει id/creationDate, θέτει state=CREATED.
2. Στη συνέχεια ο owner μπορεί επαναληπτικά (loop) να: **(α)** επεξεργαστεί πεδία (auditorium, film, start/end time) όσο state=CREATED, **(β)** να αποσύρει (withdraw) το screening — επιτρέπεται μόνο αν state=CREATED, οπότε διαγράφεται οριστικά, ή **(γ)** να το υποβάλει (submit) — επιτρέπεται μόνο αν το πρόγραμμα βρίσκεται σε SUBMISSION **και** το screening είναι πλήρες (film + auditorium + παραγόμενο end time από τη διάρκεια ταινίας)· σε επιτυχία state=SUBMITTED, αλλιώς επιστρέφεται σφάλμα.

### 4.3 Activity — Ροή Αξιολόγησης → Απόφασης Προβολής (`08-activity-screening-review-decision.excalidraw`)

Το πιο σύνθετο διάγραμμα· καλύπτει τα use cases **Assign Handler, Review, Approval, Rejection (manual & automatic), Final Submission, Acceptance**. Τέσσερα διαδικά: **Programmer**, **Staff (handler)**, **Submitter (owner)**, **System**, καθένα ενεργό στην αντίστοιχη φάση του κύκλου ζωής του Program:

1. **ASSIGNMENT**: ο Programmer αναθέτει ακριβώς έναν STAFF ως handler.
2. **REVIEW**: ο handler υποβάλλει αξιολόγηση (score + comments) → state=REVIEWED.
3. **SCHEDULING**: ο Programmer αποφασίζει έγκριση ή απόρριψη·
   - Απόρριψη (χειροκίνητη, με καταγεγραμμένη αιτιολογία) → state=REJECTED (τελική κατάσταση, τερματισμός ροής).
   - Έγκριση → state=APPROVED, η ροή συνεχίζει.
4. **FINAL_SUBMISSION**: μόνο για εγκεκριμένα screenings, ο owner υποβάλλει το τελικό πακέτο αλλαγών → τα στοιχεία «παγώνουν» (freeze).
5. **DECISION**: το σύστημα ελέγχει αν το screening είναι εγκεκριμένο **και** έχει γίνει η τελική υποβολή·
   - Αν όχι → **αυτόματη** απόρριψη από το σύστημα (state=REJECTED, τελική).
   - Αν ναι → ο Programmer κρίνει αν η τελική υποβολή καλύπτει τις απαιτούμενες αλλαγές· αν όχι → **χειροκίνητη** απόρριψη στο DECISION (state=REJECTED, τελική)· αν ναι → αποδοχή (Accept), state=SCHEDULED (τελική κατάσταση).

Το διάγραμμα αναδεικνύει καθαρά και τους δύο μηχανισμούς απόρριψης (χειροκίνητη σε SCHEDULING/DECISION, αυτόματη στο DECISION) όπως ρητά απαιτεί το εκφώνημα, καθώς και τη λογική «rejection reason must be recorded in all cases».

### 4.4 Activity — Αναζήτηση Προγραμμάτων (`09-activity-program-search.excalidraw`)

Καλύπτει το use case **Program Search**. Δέχεται προαιρετικά κριτήρια (name, description, dates, filmTitle, auditorium)· αν δεν δοθεί κανένα, επιστρέφονται όλα τα προγράμματα· αλλιώς εφαρμόζονται όλα τα δοθέντα κριτήρια με σημασιολογία **AND**. Ακολουθεί φιλτράρισμα βάσει ρόλου του αιτούντος (ο Visitor/User βλέπει μόνο ANNOUNCED, ο Programmer βλέπει επιπλέον όσα διαχειρίζεται) και ταξινόμηση **πρώτα κατά ημερομηνία, μετά κατά όνομα**, όπως ορίζει ρητά το εκφώνημα.

### 4.5 Activity — Αναζήτηση Προβολών (`10-activity-screening-search.excalidraw`)

Καλύπτει το use case **Screening Search** (εντός συγκεκριμένου προγράμματος). Κριτήρια: filmTitle, cast, genre, dateRange — προαιρετικά, με σημασιολογία **AND** μεταξύ τους· εντός κάθε πεδίου κειμένου, όλες οι λέξεις που δόθηκαν πρέπει να εμφανίζονται (case-insensitive, π.χ. `"star war"` ταιριάζει με `"Star Wars"`). Μετά το φιλτράρισμα ρόλου, η ταξινόμηση είναι **κατά genre, μετά κατά τίτλο ταινίας**, εκτός αν ζητείται προβολή χρονοδιαγράμματος (timetable view), οπότε ταξινομείται **κατά start_time**.

### 4.6–4.11 Sequence Diagrams

Όλα τα sequence diagrams ακολουθούν το ίδιο αρχιτεκτονικό μοτίβο του component diagram: **Actor → REST Resource → Service (→ AuthorizationHelper) → Repository → Database**, με συγχρονισμένα μηνύματα (συνεχής γραμμή) για κλήσεις και μηνύματα επιστροφής (διακεκομμένη γραμμή) για απαντήσεις. Οι εναλλακτικές διαδρομές (επιτυχία/σφάλμα) απεικονίζονται με πλαίσιο σύνθετου θραύσματος **alt** (κατά τη σημειογραφία UML).

- **`11-sequence-program-creation.excalidraw`** (Program Creation): ελέγχεται η μοναδικότητα του ονόματος (`existsByName`) πριν τη δημιουργία· το `alt` πλαίσιο διαχωρίζει τη διαδρομή επιτυχίας (`!exists`) από το σφάλμα 409 Conflict (`exists`). Σε επιτυχία παράγονται αυτόματα id/creationDate και ο δημιουργός γίνεται PROGRAMMER.
- **`12-sequence-add-programmer-staff.excalidraw`** (Add Programmer / Add Staff): ένα ενιαίο διάγραμμα με `alt [roleType == PROGRAMMER]` / `else [roleType == STAFF]`, δείχνοντας τον έλεγχο εξουσιοδότησης (requester ∈ PROGRAMMERS), τον έλεγχο μη-διπλής-εγγραφής, και για το STAFF, τον επιπλέον έλεγχο ότι το πρόγραμμα δεν έχει περάσει state SUBMISSION (πάγωμα συνόλου STAFF).
- **`13-sequence-program-update.excalidraw`** (Program Update): `alt` πλαίσιο ελέγχει ταυτόχρονα εξουσιοδότηση, ότι state != ANNOUNCED, και ότι ο δημιουργός παραμένει στο σύνολο PROGRAMMERS αν άλλαξαν οι ρόλοι.
- **`14-sequence-program-view.excalidraw`** (Program View): δεν έχει `alt` πλαίσιο σφάλματος αφού πρόκειται για ιδεμπότεντη, καθολικά προσβάσιμη ενέργεια· αντ' αυτού αναδεικνύεται ο ξεχωριστός συνεργάτης `AuthorizationHelper` που προσδιορίζει τον ενεργό ρόλο του αιτούντος και το επακόλουθο βήμα **redaction** (φιλτράρισμα πεδίων ανάλογα με τον ρόλο).
- **`15-sequence-program-deletion.excalidraw`** (Program Deletion): `alt` πλαίσιο ελέγχει ότι ο αιτών είναι PROGRAMMER **και** state == CREATED πριν επιτραπεί η διαγραφή.
- **`16-sequence-screening-view.excalidraw`** (Screening View): ανάλογο με το Program View· ο `AuthorizationHelper` λαμβάνει υπόψη αν ο αιτών είναι ο owner (SUBMITTER), ο ανατεθειμένος handler (STAFF), PROGRAMMER του προγράμματος, ή απλός επισκέπτης (οπότε βλέπει μόνο δημόσια πεδία εφόσον state=SCHEDULED).

---

## 5. Οντότητες Συστήματος

### 5.1 Class Diagram — `05-class-diagram.excalidraw`

Εστιάζει αποκλειστικά στις **κύριες πληροφοριακές οντότητες** και τις σχέσεις τους (χωρίς μεθόδους, όπως ζητά το εκφώνημα):

- **User**: `id, username {unique}, passwordHash, fullName`.
- **Program**: `id {auto}, name {unique}, description, startDate, endDate, creationDate {auto}, state : ProgramState`.
- **Screening**: `id {auto}, creationDate {auto}, state : ScreeningState, startTime, endTime, filmTitle, filmCast, filmGenres, filmDurationMinutes, auditoriumName, reviewScore {nullable}, reviewComments {nullable}, rejectionReason {nullable}`.
- **ProgramRole** (κλάση σύνδεσης / join entity): `id, roleType : {PROGRAMMER, STAFF}` — υλοποιεί τη σχέση πολλά-προς-πολλά μεταξύ User και Program, με το επιπλέον constraint «το πολύ ένας ρόλος ανά (user, program)».
- **Απαριθμήσεις** `ProgramState` (8 τιμές, βλ. §4.1) και `ScreeningState` (CREATED, SUBMITTED, REVIEWED, APPROVED, SCHEDULED, REJECTED).

**Σχέσεις**: `Program 1 —owns— 0..* Screening`, `User 1 —holds— 0..* ProgramRole —0..*— 1 Program`, `User 1 —submits (creator)— 0..* Screening` (υποχρεωτική — κάθε screening έχει ακριβώς έναν submitter), `User 0..1 —handles (STAFF)— 0..* Screening` (προαιρετική έως ότου γίνει η ανάθεση handler στη φάση ASSIGNMENT).

Σημείωση εντός του διαγράμματος διευκρινίζει ότι ο ρόλος SUBMITTER **δεν** αποθηκεύεται στο ProgramRole (βλ. παραδοχή §0.4), παρά προκύπτει έμμεσα από τη σχέση `Screening.submitter`.

---

## 6. Πώς να ανοίξετε/επεξεργαστείτε τα διαγράμματα

1. Μεταβείτε στο [https://excalidraw.com](https://excalidraw.com) (ή χρησιμοποιήστε την επέκταση Excalidraw για VS Code).
2. Menu → **Open** → επιλέξτε το αντίστοιχο `.excalidraw` αρχείο.
3. Για ενσωμάτωση στην αναφορά (Word/PDF): Menu → **Export image** → PNG/SVG με λευκό φόντο, ή επιλέξτε τα στοιχεία και **Copy to clipboard as PNG**.
