# Use Case Diagram — Program (Season) Management

Αναλυτική επεξήγηση: βλ. `README.md` §3.1.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif', 'background':'#ffffff', 'primaryColor':'#fef9c3', 'primaryBorderColor':'#ca8a04', 'primaryTextColor':'#713f12', 'lineColor':'#8b5cf6'}}}%%
flowchart LR
    Visitor(("👤 Visitor"))
    User(("🙋 User"))
    Programmer(("🎬 Programmer"))

    User -.->|extends| Visitor
    Programmer -.->|extends| User

    subgraph PM["📋 Program Management"]
        UC1(["🔍 Search Programs"])
        UC2(["👁️ View Program<br/>(role-based redaction)"])
        UC3(["➕ Create Program"])
        UC4(["✏️ Update Program"])
        UC5(["➕ Add Programmer"])
        UC6(["➕ Add Staff"])
        UC7(["🗑️ Delete Program<br/>(only if CREATED)"])
        UC8(["🔄 Update Program State<br/>(7 lifecycle transitions)"])
    end

    Visitor --> UC1
    Visitor --> UC2
    User --> UC3
    Programmer --> UC4
    Programmer --> UC5
    Programmer --> UC6
    Programmer --> UC7
    Programmer --> UC8

    classDef actor fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#3b0764
    classDef usecase fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#713f12
    style PM fill:#f0fdf4,stroke:#16a34a,stroke-width:2.5px,color:#14532d

    class Visitor,User,Programmer actor
    class UC1,UC2,UC3,UC4,UC5,UC6,UC7,UC8 usecase
```
