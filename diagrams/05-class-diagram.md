# Class Diagram — Main Informational Entities

Αναλυτική επεξήγηση: βλ. `README.md` §5.1. Μέθοδοι παραλείπονται σκόπιμα (μόνο attributes/relations).

```mermaid
classDiagram
    class User {
        +UUID id
        +String username
        +String passwordHash
        +String fullName
    }
    class Program {
        +UUID id
        +String name
        +String description
        +Date startDate
        +Date endDate
        +DateTime creationDate
        +ProgramState state
    }
    class ProgramRole {
        +UUID id
        +RoleType roleType
    }
    class Screening {
        +UUID id
        +DateTime creationDate
        +ScreeningState state
        +DateTime startTime
        +DateTime endTime
        +String filmTitle
        +String filmCast
        +String filmGenres
        +int filmDurationMinutes
        +String auditoriumName
        +int reviewScore
        +String reviewComments
        +String rejectionReason
    }
    class ProgramState {
        <<enumeration>>
        CREATED
        SUBMISSION
        ASSIGNMENT
        REVIEW
        SCHEDULING
        FINAL_SUBMISSION
        DECISION
        ANNOUNCED
    }
    class ScreeningState {
        <<enumeration>>
        CREATED
        SUBMITTED
        REVIEWED
        APPROVED
        SCHEDULED
        REJECTED
    }

    User "1" --> "0..*" ProgramRole : holds
    Program "1" --> "0..*" ProgramRole : assigned via
    Program "1" --> "0..*" Screening : owns
    User "1" --> "0..*" Screening : submits (creator)
    User "0..1" --> "0..*" Screening : handles (STAFF)
    Program --> ProgramState : has
    Screening --> ScreeningState : has
```

> Σημείωση: το `ProgramRole` είναι η κλάση σύνδεσης User↔Program (many-to-many) με attribute `roleType`. Ο ρόλος SUBMITTER δεν αποθηκεύεται εκεί — προκύπτει έμμεσα από τη σχέση `Screening.submitter`.
