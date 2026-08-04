# Use Case Diagram — Screening Management

Αναλυτική επεξήγηση: βλ. `README.md` §3.2.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif', 'background':'#ffffff', 'primaryColor':'#fef9c3', 'primaryBorderColor':'#ca8a04', 'primaryTextColor':'#713f12', 'lineColor':'#8b5cf6'}}}%%
flowchart LR
    Visitor(("👤 Visitor"))
    User(("🙋 User"))
    Submitter(("📤 Submitter"))
    Staff(("🧑‍💼 Staff"))
    Programmer(("🎬 Programmer"))

    User -.->|extends| Visitor
    Submitter -.->|extends| User
    Staff -.->|extends| User
    Programmer -.->|extends| User

    subgraph SM["🎞️ Screening Management"]
        UC1(["🔍 Search Screenings"])
        UC2(["👁️ View Screening<br/>(role redaction)"])
        UC3(["➕ Create Screening"])
        UC4(["✏️ Update Screening<br/>(while CREATED)"])
        UC5(["📨 Submit Screening"])
        UC6(["↩️ Withdraw Screening"])
        UC7(["📦 Final Submission<br/>(freeze)"])
        UC8(["⭐ Review Screening<br/>(score + comments)"])
        UC9(["🧑‍💼 Assign Handler<br/>(STAFF)"])
        UC10(["✅ Approve Screening"])
        UC11(["❌ Reject Screening<br/>(manual / automatic)"])
        UC12(["🗓️ Accept Screening<br/>(final scheduling)"])
    end

    Visitor --> UC1
    Visitor --> UC2
    User --> UC3
    Submitter --> UC4
    Submitter --> UC5
    Submitter --> UC6
    Submitter --> UC7
    Staff --> UC8
    Programmer --> UC9
    Programmer --> UC10
    Programmer --> UC11
    Programmer --> UC12

    classDef actor fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#3b0764
    classDef usecase fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#713f12
    classDef approve fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d
    classDef reject fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#7f1d1d
    style SM fill:#eff6ff,stroke:#2563eb,stroke-width:2.5px,color:#1e3a8a

    class Visitor,User,Submitter,Staff,Programmer actor
    class UC1,UC2,UC3,UC4,UC5,UC6,UC7,UC8,UC9,UC12 usecase
    class UC10 approve
    class UC11 reject
```
