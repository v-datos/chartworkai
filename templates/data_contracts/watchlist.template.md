# Data Quality Watchlist — {{PROJECT_NAME}}

**Owner:** {{Producer}} maintains; {{Domain Expert}} rules.

Numbered tracker for data anomalies, open questions, and quality issues. Each entry is `{{PREFIX}}-NNN` (e.g., `DQ-001`). IDs are monotonically assigned and **never reused**.

When a watchlist entry needs a binding ruling, it graduates to a file in `docs/decisions/YYYYMMDD_{{prefix}}NNN_short_title.md`.

---

## Open

| ID | Date opened | Source | Description | Severity | Owner | Status |
|---|---|---|---|---|---|---|
| DQ-NNN | {{YYYY-MM-DD}} | `data/raw/{{file}}` | {{One-line description of the anomaly. Include counts.}} | {{H/M/L}} | {{agent}} | Awaiting ruling |

---

## Decided (ruling filed; implementation pending)

| ID | Date decided | Topic | Ruling summary | Decision file | Implementer |
|---|---|---|---|---|---|
| DQ-NNN | {{date}} | {{topic}} | {{one-line}} | `docs/decisions/...` | {{agent}} |

---

## Resolved (ruling filed and implemented)

| ID | Date resolved | Topic | Ruling | Decision file | Verification |
|---|---|---|---|---|---|
| DQ-NNN | {{date}} | {{topic}} | {{one-line}} | `docs/decisions/...` | {{test or check}} |

---

## How to add a new entry

1. Reserve the next ID in the table above.
2. Add a row in **Open**: ID, date, source path, one-line description with counts, severity (H = blocks the build / corrupts results; M = affects interpretation; L = cosmetic / noted for future), and the agent best placed to escalate.
3. Notify the appropriate authority (usually {{Domain Expert}}).
4. When ruled: move row to **Decided**, file the decision in `docs/decisions/`.
5. When implemented and verified: move row to **Resolved**.

---

## Severity definitions

- **High:** silently corrupts results, breaks the build, or invalidates a published claim if not addressed.
- **Medium:** affects interpretation but doesn't break the pipeline; usually requires a documented analytic adjustment or caveat.
- **Low:** cosmetic, isolated, or already mitigated. Tracked for completeness.
