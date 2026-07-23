# Activity Diagram — Screening Review → Decision Workflow

Καλύπτει: assign handler, review, approve, reject (manual & automatic), final submission, acceptance. Αναλυτική επεξήγηση: βλ. `README.md` §4.3.

```mermaid
flowchart TD
    subgraph Programmer
        A1[Assign exactly one STAFF as handler]
        D1{Approve or Reject?<br/>program state = SCHEDULING}
        A4[Record rejection reason<br/>manual rejection]
        D3{Final submission addresses<br/>required changes?}
        A8[Manual reject<br/>state = REJECTED]
    end
    subgraph Staff["STAFF (handler)"]
        A2[Submit review: score + comments]
    end
    subgraph Submitter["SUBMITTER (owner)"]
        A6[Submit final bundle of changes]
    end
    subgraph System
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
    D1 -->|reject| A4 --> S4 --> End1((End))
    D1 -->|approve| S3 --> A6 --> S5 --> D2
    D2 -->|no| S6 --> End2((End))
    D2 -->|yes| D3
    D3 -->|no| A8 --> End3((End))
    D3 -->|yes| S7 --> End4((End))
```
