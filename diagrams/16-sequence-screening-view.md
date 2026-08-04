# Sequence Diagram — Screening View (role-based redaction)

Αναλυτική επεξήγηση: βλ. `README.md` §4.6.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif', 'background':'#ffffff', 'actorBkg':'#ede9fe', 'actorBorder':'#7c3aed', 'actorTextColor':'#3b0764', 'actorLineColor':'#8b5cf6', 'signalColor':'#8b5cf6', 'signalTextColor':'#8b5cf6', 'labelBoxBkgColor':'#dbeafe', 'labelBoxBorderColor':'#2563eb', 'labelTextColor':'#8b5cf6', 'loopTextColor':'#8b5cf6', 'noteBkgColor':'#fef9c3', 'noteBorderColor':'#ca8a04', 'noteTextColor':'#713f12', 'activationBorderColor':'#7c3aed', 'activationBkgColor':'#ede9fe', 'sequenceNumberColor':'#ffffff'}}}%%
sequenceDiagram
    autonumber
    actor Requester as Requester (Visitor/Submitter/Staff/Programmer)
    participant Res as :ScreeningRestResource
    participant Svc as :ScreeningService
    participant Auth as :AuthorizationHelper
    participant Repo as :ScreeningRepository
    participant DB as :Database

    Requester->>Res: GET /programs/{pid}/screenings/{id}
    Res->>Svc: getScreening(id, requester)
    Svc->>Repo: findById(id)
    Repo->>DB: SELECT
    DB-->>Repo: row
    Repo-->>Svc: Screening
    Svc->>Auth: determineAccess(requester, screening)
    Auth-->>Svc: accessLevel : FULL|PUBLIC|DENIED
    Svc->>Svc: redact(screening, accessLevel) -> access-appropriate DTO
    Svc-->>Res: ScreeningDTO (redacted)
    Res-->>Requester: 200 OK + screening representation (or 403/404)
```
