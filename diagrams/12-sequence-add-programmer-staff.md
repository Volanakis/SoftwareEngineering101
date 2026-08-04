# Sequence Diagram — Add Programmer / Add Staff

Αναλυτική επεξήγηση: βλ. `README.md` §4.6.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif', 'background':'#ffffff', 'actorBkg':'#ede9fe', 'actorBorder':'#7c3aed', 'actorTextColor':'#3b0764', 'actorLineColor':'#8b5cf6', 'signalColor':'#8b5cf6', 'signalTextColor':'#8b5cf6', 'labelBoxBkgColor':'#dbeafe', 'labelBoxBorderColor':'#2563eb', 'labelTextColor':'#8b5cf6', 'loopTextColor':'#8b5cf6', 'noteBkgColor':'#fef9c3', 'noteBorderColor':'#ca8a04', 'noteTextColor':'#713f12', 'activationBorderColor':'#7c3aed', 'activationBkgColor':'#ede9fe', 'sequenceNumberColor':'#ffffff'}}}%%
sequenceDiagram
    autonumber
    actor Programmer
    participant Res as :ProgramRestResource
    participant Svc as :ProgramService
    participant URepo as :UserRepository
    participant PRepo as :ProgramRepository
    participant DB as :Database

    Programmer->>Res: POST /programs/{id}/roles {userId, roleType}
    Res->>Svc: addRole(programId, userId, roleType, requester)
    Svc->>Svc: check requester in PROGRAMMERS set
    Svc->>URepo: findById(userId)
    URepo->>DB: SELECT
    DB-->>URepo: row
    URepo-->>Svc: User
    alt roleType == PROGRAMMER
        Svc->>Svc: check user not already a PROGRAMMER
        Svc->>PRepo: addProgrammer(program, user)
        PRepo->>DB: UPDATE program_roles
        DB-->>PRepo: OK
    else roleType == STAFF
        Svc->>Svc: check program.state == CREATED (STAFF set frozen after SUBMISSION)
        Svc->>PRepo: addStaff(program, user) [only if allowed]
        PRepo->>DB: UPDATE program_roles
        DB-->>PRepo: OK (or Service returns 409 if STAFF set frozen)
    end
    PRepo-->>Svc: updated Program
    Svc-->>Res: ProgramDTO
    Res-->>Programmer: 200 OK (or 409 error)
```
