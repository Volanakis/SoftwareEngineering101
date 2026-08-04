# Sequence Diagram — Program View (role-based redaction)

Αναλυτική επεξήγηση: βλ. `README.md` §4.6.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif', 'actorBkg':'#ede9fe', 'actorBorder':'#7c3aed', 'actorTextColor':'#3b0764', 'actorLineColor':'#a78bfa', 'signalColor':'#334155', 'signalTextColor':'#1e293b', 'labelBoxBkgColor':'#dbeafe', 'labelBoxBorderColor':'#2563eb', 'labelTextColor':'#1e3a8a', 'loopTextColor':'#1e3a8a', 'noteBkgColor':'#fef9c3', 'noteBorderColor':'#ca8a04', 'noteTextColor':'#713f12', 'activationBorderColor':'#7c3aed', 'activationBkgColor':'#ede9fe', 'sequenceNumberColor':'#ffffff'}}}%%
sequenceDiagram
    autonumber
    actor Requester as Requester (Visitor/User/Programmer/Staff)
    participant Res as :ProgramRestResource
    participant Svc as :ProgramService
    participant Auth as :AuthorizationHelper
    participant Repo as :ProgramRepository
    participant DB as :Database

    Requester->>Res: GET /programs/{id}
    Res->>Svc: getProgram(id, requester)
    Svc->>Repo: findById(id)
    Repo->>DB: SELECT
    DB-->>Repo: row
    Repo-->>Svc: Program
    Svc->>Auth: determineRole(requester, program)
    Auth-->>Svc: role : VISITOR|PROGRAMMER|STAFF|SUBMITTER
    Svc->>Svc: redact(program, role) -> role-appropriate DTO
    Svc-->>Res: ProgramDTO (redacted per role)
    Res-->>Requester: 200 OK + program representation
```
