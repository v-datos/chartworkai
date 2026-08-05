# Lineage — {{PROJECT_NAME}}

**Owner:** {{Producer role}}.

Trace from every processed column back to its raw source(s) and transformation. The lineage doc answers "where did this number come from?" without requiring a code dive.

---

## Conventions

- One section per processed table.
- For each column: `processed_col` ← `raw_file::raw_col` `[transform]`
- Multi-source columns list all inputs.
- Derived columns include the formula or pseudocode.

---

## Table: `{{processed_table_1}}`

| Processed column | Source | Transform |
|---|---|---|
| `{{col_1}}` | `{{raw_file}}::{{Col}}` | identity (rename only) |
| `{{col_2}}` | `{{raw_file}}::{{ColA}}, {{ColB}}` | `{{ColA}} + {{ColB}}` |
| `{{col_3}}` | `{{raw_file}}::{{Col}}` | unit conversion: {{from}} → {{to}} via {{formula}} |
| `{{col_4}}` | derived | `1 - sum({{conditions}}) / total` (see DQ-NNN for substitution rule) |
| `build_version` | constant | passed at build time |

---

## Table: `{{processed_table_2}}`

| Processed column | Source | Transform |
|---|---|---|
| | | |

---

## External-source joins

| Processed column | External source | Join key | Alignment |
|---|---|---|---|
| `{{col}}` | `data/external/{{source}}/...` | `{{station_id, year}}` | {{nearest pixel | exact match | etc.}} |

---

## Known divergences from raw

For columns where the processed value intentionally differs from the raw equivalent (e.g., due to a DQ ruling), document here:

- `{{col}}`: raw shows {{X}} for {{N rows}}; processed value is {{Y}} per ruling DQ-NNN.
