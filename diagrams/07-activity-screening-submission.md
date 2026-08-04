# Activity Diagram — Screening Submission Workflow

Καλύπτει: creation, update, submission, withdrawal. Αναλυτική επεξήγηση: βλ. `README.md` §4.2.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif', 'background':'#ffffff', 'primaryColor':'#dbeafe', 'primaryBorderColor':'#2563eb', 'primaryTextColor':'#1e3a8a', 'lineColor':'#64748b'}}}%%
flowchart TD
    subgraph Submitter["📤 SUBMITTER (owner)"]
        A1[Create screening: select program + initial fields]
        A2[Edit editable fields: auditorium, film, start/end time]
        A5[Delete screening<br/>not entered formal review]
    end
    subgraph System["⚙️ System"]
        A3[Auto-assign SUBMITTER role;<br/>id, creationDate auto-generated; state = CREATED]
        D2{program.state == SUBMISSION AND<br/>screening complete?}
        A6[state = SUBMITTED; persist & audit log]
        E1[Return error: incomplete/wrong state]
    end

    Start((Start)) --> A1 --> A3 --> D1{Owner chooses:<br/>Update / Submit / Withdraw}
    D1 -->|"update"| A2 -->|"loop while CREATED"| D1
    D1 -->|"withdraw"| D3{state == CREATED?}
    D3 -->|"yes"| A5 --> End1((End))
    D3 -->|"no n/a"| End2((End))
    D1 -->|"submit"| D2
    D2 -->|"yes"| A6 --> End3((End))
    D2 -->|"no"| E1 --> End4((End))

    classDef startNode fill:#22c55e,stroke:#15803d,stroke-width:2px,color:#ffffff,font-weight:bold
    classDef successEnd fill:#16a34a,stroke:#14532d,stroke-width:2px,color:#ffffff,font-weight:bold
    classDef errorEnd fill:#ef4444,stroke:#7f1d1d,stroke-width:2px,color:#ffffff,font-weight:bold
    classDef neutralEnd fill:#64748b,stroke:#334155,stroke-width:2px,color:#ffffff,font-weight:bold
    classDef action fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a8a
    classDef decision fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f
    classDef errorAction fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#7f1d1d
    classDef successAction fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d
    style Submitter fill:#fff7ed,stroke:#ea580c,stroke-width:2px,color:#7c2d12
    style System fill:#eff6ff,stroke:#2563eb,stroke-width:2px,color:#1e3a8a

    class Start startNode
    class End3 successEnd
    class End2,End4 errorEnd
    class End1 neutralEnd
    class D1,D2,D3 decision
    class A1,A2,A3 action
    class A5 neutralEnd
    class E1 errorAction
    class A6 successAction
```
