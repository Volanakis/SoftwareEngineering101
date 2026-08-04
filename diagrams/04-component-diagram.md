# Component Diagram — System Architecture

Αναλυτική επεξήγηση: βλ. `README.md` §2.2.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif', 'primaryColor':'#eff6ff', 'primaryBorderColor':'#2563eb', 'primaryTextColor':'#1e3a8a', 'lineColor':'#64748b'}}}%%
flowchart TD
    Client["💻 Client Applications<br/>(HTTP / REST clients)"]

    subgraph GW["🛡️ Gateway (cross-cutting)"]
        Auth["🔐 Authentication & Authorization Filter<br/>(Flask before_request hook)"]
        Rate["⏱️ Rate Limiter<br/>(Flask-Limiter)"]
    end

    subgraph REST["🌐 Presentation Layer"]
        ProgRes["📡 Program REST Resource<br/>(Flask Blueprint)"]
        ScrRes["📡 Screening REST Resource<br/>(Flask Blueprint)"]
    end

    subgraph SVC["⚙️ Service Layer"]
        ProgSvc["🧠 Program Service<br/>(state-machine rules,<br/>search/redaction logic)"]
        ScrSvc["🧠 Screening Service<br/>(state-machine rules,<br/>search/redaction logic)"]
    end

    Log["📝 Logging & Audit Component<br/>(error handling, audit trail)"]

    subgraph REPO["🗃️ Data Access Layer"]
        ProgRepo["📚 Program Repository<br/>(SQLAlchemy)"]
        ScrRepo["📚 Screening Repository<br/>(SQLAlchemy)"]
        UserRepo["📚 User Repository<br/>(SQLAlchemy, read-mostly)"]
    end

    DB[("🗄️ Cinema Relational Database<br/>(Programs, Screenings, Users, ProgramRoles)")]
    Ext[["🌍 External User Management System"]]

    Client -->|"HTTPS/JSON"| Auth
    Auth -->|"authorize"| ProgRes
    Auth -->|"authorize"| ScrRes
    Rate -->|"throttle"| ScrRes
    Auth -->|"verify credentials"| UserRepo
    ProgRes -->|"delegates"| ProgSvc
    ScrRes -->|"delegates"| ScrSvc
    ScrSvc -->|"reads program state"| ProgSvc
    ProgSvc -->|"audit log, both services"| Log
    ProgSvc -->|"persist"| ProgRepo
    ScrSvc -->|"persist"| ScrRepo
    ProgRepo -->|"SQL"| DB
    ScrRepo -->|"SQL"| DB
    UserRepo -->|"SQL"| DB
    UserRepo -->|"sync / verify"| Ext

    classDef client fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#3b0764
    classDef gateway fill:#ffedd5,stroke:#ea580c,stroke-width:2px,color:#7c2d12
    classDef presentation fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a8a
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d
    classDef logging fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#831843
    classDef repo fill:#ccfbf1,stroke:#0d9488,stroke-width:2px,color:#134e4a
    classDef datastore fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f
    classDef external fill:#f1f5f9,stroke:#64748b,stroke-width:2px,stroke-dasharray:5 3,color:#334155

    style GW fill:#fff7ed,stroke:#ea580c,stroke-width:2px,color:#7c2d12
    style REST fill:#eff6ff,stroke:#2563eb,stroke-width:2px,color:#1e3a8a
    style SVC fill:#f0fdf4,stroke:#16a34a,stroke-width:2px,color:#14532d
    style REPO fill:#f0fdfa,stroke:#0d9488,stroke-width:2px,color:#134e4a

    class Client client
    class Auth,Rate gateway
    class ProgRes,ScrRes presentation
    class ProgSvc,ScrSvc service
    class Log logging
    class ProgRepo,ScrRepo,UserRepo repo
    class DB datastore
    class Ext external
```
