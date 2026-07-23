# Contributing Guide

Οδηγός συνεργασίας για την ομάδα (1-2 άτομα) που υλοποιεί το Cinema Management Backend System.

## Git Workflow

- **Καμία απευθείας δουλειά πάνω στο `main`.** Κάθε άτομο δουλεύει στο δικό του feature branch.
- Branch naming: `feature/<σύντομη-περιγραφή>`, π.χ. `feature/program-mgmt`, `feature/screening-mgmt`, `feature/rate-limiting`.
- Άνοιγμα Pull Request για κάθε branch πριν το merge στο `main`. **Κανένα PR δεν πρέπει να γίνεται merge αυτόματα** — να ελέγχεται και να εγκρίνεται χειροκίνητα από το άλλο μέλος της ομάδας πριν το merge.
- Commit messages: σύντομος τίτλος στην προστακτική (π.χ. `Add program state-transition endpoint`), όχι γενικόλογα μηνύματα.
- Πριν το merge, το branch πρέπει να περνάει το CI (`pytest` + οποιοδήποτε lint step) χωρίς σφάλματα.

### Σημείωση ασφαλείας (σημαντικό)

Αν έχετε συνδέσει οποιοδήποτε αυτοματοποιημένο εργαλείο/bot/agent integration με δικαιώματα push στο repository (π.χ. MCP integrations, hooks, CI bots που κάνουν auto-commit/auto-merge), **επιβεβαιώστε ρητά τι δικαιώματα έχει** πριν το αφήσετε να τρέχει χωρίς επίβλεψη. Οποιοδήποτε commit ή merge στο `main` πρέπει να είναι ρητά αποτέλεσμα ανθρώπινης ενέργειας (χειροκίνητο `git push` / merge button στο GitHub UI), όχι αυτόνομης ενέργειας εργαλείου.

## Δομή Εργασιών

Δείτε το [`TASKS.md`](TASKS.md) για τον πλήρη καταμερισμό εργασιών ανά άτομο (Person A: Program Management, Person B: Screening Management) και τις φάσεις υλοποίησης.

## Πριν ανοίξετε PR

- [ ] `pytest` περνάει τοπικά
- [ ] Νέες λειτουργίες συνοδεύονται από unit tests
- [ ] Κώδικας ακολουθεί τη δομή `models/ services/ blueprints/ tests/`
- [ ] Δεν έγιναν αλλαγές εκτός του δικού σας module χωρίς συνεννόηση (αποφυγή merge conflicts)

## Τοπική Εκτέλεση

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest
```
