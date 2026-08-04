# Class Diagram — Main Informational Entities

Αναλυτική επεξήγηση: βλ. `README.md` §5.1. Μέθοδοι παραλείπονται σκόπιμα (μόνο attributes/relations).

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif', 'classText':'#1e293b'}}}%%
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

    cssClass "User" entity
    cssClass "Program" entity
    cssClass "Screening" entity
    cssClass "ProgramRole" joinEntity
    cssClass "ProgramState" enumeration
    cssClass "ScreeningState" enumeration

    classDef entity fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a8a
    classDef joinEntity fill:#ccfbf1,stroke:#0d9488,stroke-width:2px,color:#134e4a
    classDef enumeration fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f
```

> Σημείωση: το `ProgramRole` είναι η κλάση σύνδεσης User↔Program (many-to-many) με attribute `roleType`. Ο ρόλος SUBMITTER δεν αποθηκεύεται εκεί — προκύπτει έμμεσα από τη σχέση `Screening.submitter`.
