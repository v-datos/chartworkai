# Style Guide — {{PROJECT_NAME}}

## Colors

Project palette. Define as constants in your viz module so figures stay consistent.

| Token | Hex | Use |
|---|---|---|
| `{{TOKEN_1}}` | `#XXXXXX` | {{purpose}} |
| `{{TOKEN_2}}` | `#XXXXXX` | {{purpose}} |
| `HIGHLIGHT` | `#F39C12` | Annotations, callouts |
| `NEUTRAL` | `#7F8C8D` | Background, non-significant series |

Colorblind-safe: all categorical palette combinations must pass WCAG AA contrast and remain distinguishable in deuteranopia simulation.

## Fonts

- Body / axis labels: **{{primary font}}** (system fallback: Helvetica Neue, Arial)
- Math / equations: **{{math font}}** via matplotlib `mathtext` (or equivalent)
- Font sizes: title 14pt, axis label 12pt, tick label 10pt, annotation 9pt

## Figure dimensions

| Context | Width × Height | DPI |
|---|---|---|
| Journal single-column | 86 mm × auto | 300 |
| Journal double-column | 178 mm × auto | 300 |
| Presentation slide | 16 cm × 9 cm | 150 |
| Dashboard tile | 400 px × 300 px | 96 |

Always save as both SVG (vector, `reports/figures/`) and PNG (300 dpi, same dir).

## File naming

- Figures: `{phase}_{figure_id}_{descriptor}.svg` — e.g. `03_fig01_{{descriptor}}.svg`
- Notebooks: `{phase:02d}_{descriptor}.ipynb`
- Processed tables: snake_case, no version in filename (track version inside `build_version` column)
- Raw data: never rename; keep original source filenames

## Code style

- Line length: {{100}} characters (linter enforced)
- String quotes: {{double}} (linter enforced)
- Type hints: required for all public functions in `src/{{PROJECT_SLUG}}/`
- No inline comments that describe *what* code does; only *why* (non-obvious constraints)

## Units

Always store and compute in canonical units:

| Quantity | Unit | Notes |
|---|---|---|
| {{Quantity 1}} | {{unit}} | {{}} |
| {{Quantity 2}} | {{unit}} | {{}} |
| Proportions | `[0, 1]` | never percent in processed tables |
| Dates | ISO 8601 | |
| Coordinates (if geospatial) | decimal degrees, EPSG:4326 | |

## Decision log convention

Every non-trivial methodological choice goes in `docs/decisions/` as `YYYYMMDD_short_title.md`. See [`templates/decisions/YYYYMMDD_decision.template.md`](decisions/YYYYMMDD_decision.template.md).

Format: **Context** → **Ruling** → **Rationale** → **Instruction** (concrete next steps for whoever implements).
