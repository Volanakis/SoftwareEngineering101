# Activity Diagram — Program Search

Αναλυτική επεξήγηση: βλ. `README.md` §4.4.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif', 'background':'#ffffff', 'primaryColor':'#dbeafe', 'primaryBorderColor':'#2563eb', 'primaryTextColor':'#1e3a8a', 'lineColor':'#64748b'}}}%%
flowchart TD
    Start((Start)) --> A1[Receive search request: optional name,<br/>description, dates, filmTitle, auditorium<br/>+ requester role]
    A1 --> D1{Any search criteria supplied?}
    D1 -->|"no"| A2[Select ALL programs]
    D1 -->|"yes"| A3[Apply AND-combined filters<br/>on all supplied parameters]
    A2 --> A4[Filter results by requester's role]
    A3 --> A4
    A4 --> A5[Sort: by date, then by name]
    A5 --> A6[Return filtered, sorted program list]
    A6 --> End((End))

    classDef startNode fill:#22c55e,stroke:#15803d,stroke-width:2px,color:#ffffff,font-weight:bold
    classDef successEnd fill:#16a34a,stroke:#14532d,stroke-width:2px,color:#ffffff,font-weight:bold
    classDef action fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a8a
    classDef decision fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f
    classDef successAction fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d

    class Start startNode
    class End successEnd
    class D1 decision
    class A1,A2,A3,A4,A5 action
    class A6 successAction
```
