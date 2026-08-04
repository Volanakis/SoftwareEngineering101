# Activity Diagram — Screening Review → Decision Workflow

Καλύπτει: assign handler, review, approve, reject (manual & automatic), final submission, acceptance. Αναλυτική επεξήγηση: βλ. `README.md` §4.3.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif', 'primaryColor':'#dbeafe', 'primaryBorderColor':'#2563eb', 'primaryTextColor':'#1e3a8a', 'lineColor':'#64748b'}}}%%
flowchart TD
    subgraph Programmer["🎬 Programmer"]
        A1[Assign exactly one STAFF as handler]
        D1{Approve or Reject?<br/>program state = SCHEDULING}
        A4[Record rejection reason<br/>manual rejection]
        D3{Final submission addresses<br/>required changes?}
        A8[Manual reject<br/>state = REJECTED]
    end
    subgraph Staff["🧑‍💼 STAFF (handler)"]
        A2[Submit review: score + comments]
    end
    subgraph Submitter["📤 SUBMITTER (owner)"]
        A6[Submit final bundle of changes]
    end
    subgraph System["⚙️ System"]
        S1[Set screening.handler; persist]
        S2[state = REVIEWED]
        S3[state = APPROVED]
        S4[state = REJECTED, final]
        S5[Freeze screening details]
        D2{Program state = DECISION:<br/>approved AND finally submitted?}
        S6[AUTOMATIC rejection:<br/>state = REJECTED, final]
        S7[Accept: state = SCHEDULED, final]
    end

    Start((Start)) --> A1 --> S1 --> A2 --> S2 --> D1
    D1 -->|"reject"| A4 --> S4 --> End1((End))
    D1 -->|"approve"| S3 --> A6 --> S5 --> D2
    D2 -->|"no"| S6 --> End2((End))
    D2 -->|"yes"| D3
    D3 -->|"no"| A8 --> End3((End))
    D3 -->|"yes"| S7 --> End4((End))

    classDef startNode fill:#22c55e,stroke:#15803d,stroke-width:2px,color:#ffffff,font-weight:bold
    classDef successEnd fill:#16a34a,stroke:#14532d,stroke-width:2px,color:#ffffff,font-weight:bold
    classDef errorEnd fill:#ef4444,stroke:#7f1d1d,stroke-width:2px,color:#ffffff,font-weight:bold
    classDef action fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a8a
    classDef decision fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f
    classDef errorAction fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#7f1d1d
    classDef successAction fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d
    style Programmer fill:#f5f3ff,stroke:#7c3aed,stroke-width:2px,color:#3b0764
    style Staff fill:#f0fdfa,stroke:#0d9488,stroke-width:2px,color:#134e4a
    style Submitter fill:#fff7ed,stroke:#ea580c,stroke-width:2px,color:#7c2d12
    style System fill:#eff6ff,stroke:#2563eb,stroke-width:2px,color:#1e3a8a

    class Start startNode
    class End4 successEnd
    class End1,End2,End3 errorEnd
    class D1,D2,D3 decision
    class A1,A2,A6,S1,S2,S3,S5 action
    class A4,A8,S4,S6 errorAction
    class S7 successAction
```
