# Data Dictionary — {{PROJECT_NAME}}

**Owner:** {{Producer role — e.g., Data Engineer}}
**Status:** Living document. Update on every schema change. Never lag the actual schema.

This document is the canonical reference for every column in every processed artifact. Any agent that consumes a processed artifact reads this first.

---

## How to read this document

- One section per processed table.
- One row per column.
- Columns: name, type, units, nullable?, range/domain, source (raw column or derivation), description, decision references.

---

## Table: `{{processed_table_1}}`

**Path:** `data/processed/{{table_name}}.parquet`
**Grain:** one row per `{{primary_key_tuple}}`.
**Build:** produced by `src/{{PROJECT_SLUG}}/transform/{{module}}.py` from {{raw inputs}}.
**Reproducible from raw via:** `make {{target}}`.

### Columns

| Column | Type | Units | Nullable? | Range / Domain | Source | Description | Decisions |
|---|---|---|---|---|---|---|---|
| `{{col_1}}` | int | — | No | ≥ 0 | raw `{{Col}}` | {{Description}} | — |
| `{{col_2}}` | float | {{unit}} | Yes | [0, 1] | derived: {{formula}} | {{Description}} | DQ-NNN |
| `build_version` | str | — | No | — | constant | Build identifier | — |

### Notes

{{Any table-level caveats. Methodology changes that affect this table. Aggregations. Deduplication rules.}}

---

## Table: `{{processed_table_2}}`

**Path:** `data/processed/{{table_name}}.parquet`
**Grain:** {{}}
**Build:** {{}}

### Columns

| Column | Type | Units | Nullable? | Range / Domain | Source | Description | Decisions |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

---

## Cross-table relationships

```
{{table_1}}.{{key}}  ─┬─►  {{table_2}}.{{key}}
                       └─►  {{master_table}}.{{key}}
```

Describe foreign-key relationships and any cascading constraints.

---

## Change log

| Date | Table | Change | Decision |
|---|---|---|---|
| {{date}} | {{table}} | Added column `{{name}}` | DQ-NNN |
| {{date}} | {{table}} | Renamed `{{old}}` → `{{new}}` | DQ-NNN |
