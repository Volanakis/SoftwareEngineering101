# Sequence Diagram — Program Creation

Αναλυτική επεξήγηση: βλ. `README.md` §4.6.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif', 'background':'#ffffff', 'actorBkg':'#ede9fe', 'actorBorder':'#7c3aed', 'actorTextColor':'#3b0764', 'actorLineColor':'#8b5cf6', 'signalColor':'#8b5cf6', 'signalTextColor':'#8b5cf6', 'labelBoxBkgColor':'#dbeafe', 'labelBoxBorderColor':'#2563eb', 'labelTextColor':'#8b5cf6', 'loopTextColor':'#8b5cf6', 'noteBkgColor':'#fef9c3', 'noteBorderColor':'#ca8a04', 'noteTextColor':'#713f12', 'activationBorderColor':'#7c3aed', 'activationBkgColor':'#ede9fe', 'sequenceNumberColor':'#ffffff'}}}%%
sequenceDiagram
    autonumber
    actor User
    participant Res as :ProgramRestResource
    participant Svc as :ProgramService
    participant Repo as :ProgramRepository
    participant DB as :Database

    User->>Res: POST /programs {name, description, dates}
    Res->>Svc: createProgram(dto, currentUser)
    Svc->>Repo: existsByName(name)
    Repo->>DB: SELECT ... WHERE name = ?
    DB-->>Repo: result
    Repo-->>Svc: exists : boolean
    alt name is unique
        Svc->>Svc: validate required fields, generate id/creationDate, set state = CREATED
        Svc->>Repo: save(program, creator as PROGRAMMER)
        Repo->>DB: INSERT
        DB-->>Repo: OK
        Repo-->>Svc: saved Program
        Svc-->>Res: ProgramDTO (201 Created)
    else name already taken
        Svc-->>Res: 409 Conflict
    end
    Res-->>User: HTTP response (201 + body, or 409 error)
```
