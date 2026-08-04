# Context Diagram — Cinema Management Backend System

Αναλυτική επεξήγηση: βλ. `README.md` §2.1.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif', 'primaryColor':'#eef2ff', 'primaryBorderColor':'#4338ca', 'primaryTextColor':'#1e1b4b', 'lineColor':'#6366f1'}}}%%
flowchart LR
    Visitor(("👤 Visitor<br/>(anonymous)"))
    RegUser(("🔐 Registered User<br/>(User / Programmer /<br/>Staff / Submitter)"))
    Sys["🎬 Cinema Management<br/>Backend System<br/>(RESTful Web Services)"]
    UserMgmt[["🗂️ User Management System<br/>(external)"]]
    DB[("🗄️ Cinema Relational Database<br/>(shared Users table)")]

    Visitor -->|"search / view ANNOUNCED programs<br/>& SCHEDULED screenings"| Sys
    RegUser -->|"authenticate; create/manage<br/>programs & screenings"| Sys
    Sys <-->|"verify credentials;<br/>read/write program-specific roles"| UserMgmt
    Sys <-->|"CRUD program & screening data<br/>(transactional)"| DB

    classDef actor fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#3b0764
    classDef boundary fill:#dbeafe,stroke:#2563eb,stroke-width:2.5px,color:#1e3a8a,font-weight:bold
    classDef external fill:#f1f5f9,stroke:#64748b,stroke-width:2px,stroke-dasharray:5 3,color:#334155
    classDef datastore fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f

    class Visitor,RegUser actor
    class Sys boundary
    class UserMgmt external
    class DB datastore
```
