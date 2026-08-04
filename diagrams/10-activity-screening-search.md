# Activity Diagram — Screening Search

Αναλυτική επεξήγηση: βλ. `README.md` §4.5.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif', 'background':'#ffffff', 'primaryColor':'#dbeafe', 'primaryBorderColor':'#2563eb', 'primaryTextColor':'#1e3a8a', 'lineColor':'#64748b'}}}%%
flowchart TD
    Start((Start)) --> A1[Receive search request within a program:<br/>optional filmTitle, cast, genre, dateRange<br/>+ requester role]
    A1 --> D1{Any filters supplied?}
    D1 -->|"no"| A2[Select ALL screenings of the program]
    D1 -->|"yes"| A3[Apply AND-combined filters;<br/>word-subset, case-insensitive match per text field]
    A2 --> A4[Filter results by requester's role]
    A3 --> A4
    A4 --> D2{Timetable view requested?}
    D2 -->|"yes"| A5[Sort by start_time]
    D2 -->|"no"| A6[Sort by film genre, then film title]
    A5 --> A7[Return filtered, sorted screening list]
    A6 --> A7
    A7 --> End((End))

    classDef startNode fill:#22c55e,stroke:#15803d,stroke-width:2px,color:#ffffff,font-weight:bold
    classDef successEnd fill:#16a34a,stroke:#14532d,stroke-width:2px,color:#ffffff,font-weight:bold
    classDef action fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a8a
    classDef decision fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f
    classDef successAction fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d

    class Start startNode
    class End successEnd
    class D1,D2 decision
    class A1,A2,A3,A4,A5,A6 action
    class A7 successAction
```
