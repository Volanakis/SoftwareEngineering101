# Sequence Diagram — Program Update

Αναλυτική επεξήγηση: βλ. `README.md` §4.6.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif', 'background':'#ffffff', 'actorBkg':'#ede9fe', 'actorBorder':'#7c3aed', 'actorTextColor':'#3b0764', 'actorLineColor':'#8b5cf6', 'signalColor':'#8b5cf6', 'signalTextColor':'#8b5cf6', 'labelBoxBkgColor':'#dbeafe', 'labelBoxBorderColor':'#2563eb', 'labelTextColor':'#8b5cf6', 'loopTextColor':'#8b5cf6', 'noteBkgColor':'#fef9c3', 'noteBorderColor':'#ca8a04', 'noteTextColor':'#713f12', 'activationBorderColor':'#7c3aed', 'activationBkgColor':'#ede9fe', 'sequenceNumberColor':'#ffffff'}}}%%
sequenceDiagram
    autonumber
    actor Programmer
    participant Res as :ProgramRestResource
    participant Svc as :ProgramService
    participant Repo as :ProgramRepository
    participant DB as :Database

    Programmer->>Res: PUT /programs/{id} {name?, description?, dates?, roles?}
    Res->>Svc: updateProgram(id, dto, requester)
    Svc->>Repo: findById(id)
    Repo->>DB: SELECT
    DB-->>Repo: row
    Repo-->>Svc: Program
    alt authorized and state is not ANNOUNCED and creator kept
        Svc->>Svc: check requester in PROGRAMMERS, state != ANNOUNCED, creator kept in PROGRAMMERS
        Svc->>Repo: save(updatedProgram)
        Repo->>DB: UPDATE
        DB-->>Repo: OK
        Repo-->>Svc: saved Program
        Svc-->>Res: ProgramDTO
    else unauthorized / ANNOUNCED / creator removal attempt
        Svc-->>Res: 403/409 error
    end
    Res-->>Programmer: 200 OK (or error)
```
