# Activity Diagram — Program Lifecycle State Update

Καλύπτει το use case Program State Update (7 μεταβάσεις). Αναλυτική επεξήγηση: βλ. `README.md` §4.1.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif', 'primaryColor':'#dbeafe', 'primaryBorderColor':'#2563eb', 'primaryTextColor':'#1e3a8a', 'lineColor':'#64748b'}}}%%
flowchart TD
    subgraph Programmer["🎬 Programmer"]
        A1[Select target state & submit transition request]
    end
    subgraph System["⚙️ System"]
        D1{Requester ∈ PROGRAMMERS set?}
        E1[Return 403 Unauthorized]
        D2{Transition matches allowed sequence?<br/>no rollback, no skipping}
        E2[Return 409 Invalid transition]
        A2[Apply transition side-effects]
        D3{Target state == DECISION?}
        A3[Auto-reject APPROVED screenings<br/>not finally submitted]
        A4[Persist new state, timestamp & audit log]
        A5[Return 200 OK + updated program]
    end

    Start((Start)) --> A1 --> D1
    D1 -->|"no"| E1 --> End1((End))
    D1 -->|"yes"| D2
    D2 -->|"no"| E2 --> End2((End))
    D2 -->|"yes"| A2 --> D3
    D3 -->|"yes"| A3 --> A4
    D3 -->|"no"| A4
    A4 --> A5 --> End3((End))

    classDef startNode fill:#22c55e,stroke:#15803d,stroke-width:2px,color:#ffffff,font-weight:bold
    classDef successEnd fill:#16a34a,stroke:#14532d,stroke-width:2px,color:#ffffff,font-weight:bold
    classDef errorEnd fill:#ef4444,stroke:#7f1d1d,stroke-width:2px,color:#ffffff,font-weight:bold
    classDef action fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a8a
    classDef decision fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f
    classDef errorAction fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#7f1d1d
    classDef successAction fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d
    style Programmer fill:#f5f3ff,stroke:#7c3aed,stroke-width:2px,color:#3b0764
    style System fill:#eff6ff,stroke:#2563eb,stroke-width:2px,color:#1e3a8a

    class Start startNode
    class End3 successEnd
    class End1,End2 errorEnd
    class D1,D2,D3 decision
    class A1,A2,A3,A4 action
    class E1,E2 errorAction
    class A5 successAction
```
