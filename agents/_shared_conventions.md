# Shared Conventions (template)

This file is meant to be copied into the **Shared Conventions** section of your project's `AGENTS.md`. Customize the placeholders.

Every agent operates within these rules. Violations escalate to the Orchestrator.

---

## Repository layout

All paths relative to repo root `{{PROJECT_SLUG}}/`. The tree below is the **data-science** profile's layout; other profiles use their idiomatic layout — only the `docs/` operating structure is universal (see `profiles/`):

```
data/
  raw/                       # Immutable source data
  external/{source}/         # Third-party datasets with MANIFEST per source
  interim/                   # Intermediate build artifacts
  processed/                 # Canonical processed outputs
src/{{PROJECT_SLUG}}/        # Project package
  io/                        # Loaders + schema validators
  transform/                 # Cleaning, joining, aggregation
  features/                  # Derived metrics
  models/                    # Statistical / causal / forecasting modules
  viz/                       # Reusable plotting
tests/                       # Test suite + fixtures
notebooks/                   # Numbered by phase (e.g., 01_eda_*, 02_*)
reports/
  figures/                   # Publication-grade outputs (SVG + PNG)
  tables/                    # Result tables
  draft/                     # In-progress narrative
docs/
  decisions/                 # Authority-stamped rulings
  handoffs/                  # Inter-agent artifact notices
  data/                      # Data dictionary, watchlist, lineage
  domain/                    # Domain knowledge artifacts
  reproducibility/           # Per-phase reproduce reports
PROJECT_CHARTER.md
AGENTS.md
STATUS.md
TASKS.md
docs/phase_plan.md
```

## Canonical processed artifacts

Every analytic agent consumes these, never raw data directly. {{List the project's canonical tables / artifacts here.}}

## Keys, types, units

- {{Primary key conventions}}
- {{Type conventions: integers vs floats vs strings}}
- {{Unit conventions: SI / canonical}}
- {{Coordinate reference system if geospatial}}
- {{Date format: ISO 8601}}

## Tooling

Declared in the charter `## Stack` block — fill for your stack, any language:

- Language / runtime: {{language and version}}
- Package / environment manager: {{package manager and lockfile}}
- Core stack: {{key libraries or frameworks}}
- Linter / formatter: {{linter}}
- Type checker: {{type checker, if any}}

## Code style

- Line length: {{100}}
- String quotes: {{double}}
- Type hints: required for all public functions in `src/{{PROJECT_SLUG}}/`
- Docstrings: required for public functions; include parameter types and a one-line example
- No inline comments describing *what* code does; only *why*

## Notebooks rule

*(Data-science profile.)* Notebooks are for exploration and narrative. Any function used more than once moves to `src/{{PROJECT_SLUG}}/`. Notebooks must never import from other notebooks; the verify command flags this.

## Living-documents rule (update-in-place, never append)

**This is non-negotiable. Violating it corrupts the project's source of truth.**

The following documents have a **single canonical form** and are updated **in place**, never by appending a new copy of a section:

- `PROJECT_CHARTER.md`
- `AGENTS.md`
- `docs/phase_plan.md`
- `docs/data/data_dictionary.md`
- `docs/data/lineage.md`
- `docs/data/watchlist.md`
- `docs/style_guide.md`
- `STATUS.md` (only the **top entry** is the current week; older weeks accumulate below as a log)
- `TASKS.md` (each section is a single canonical list; tasks **move** between sections, never duplicate)

Rules every agent must follow when touching these files:

1. **Read the file fully before editing.** No exceptions. If the file is too long to read in full, that itself is a signal that prior agents have appended duplicates — prune before adding.
2. **Use targeted edits (find-and-replace within a section), not append.** Never `>>` append. Never paste a fresh full template on top of existing content.
3. **One canonical instance per section.** If a section is named "Phase N checklist" or "Active agents", there is exactly **one** such section in the file. If you are about to write a second one, you are doing it wrong — overwrite the existing one instead.
4. **Idempotency check before saving.** Before writing, scan for duplicate H2/H3 headings (`## ...`, `### ...`). If any heading appears more than once and the document type forbids it (everything in this list except STATUS.md week-entries), consolidate to a single section first.
5. **Date-stamped updates** (handoffs, decisions, weekly STATUS entries) are the **only** documents allowed to grow by accretion — and even those grow by **prepending** a new dated entry, never by duplicating an existing one.
6. **When regenerating from a prompt**, supply the prompt with the **current file contents** and ask for an **updated version**, not for a fresh draft to paste onto the end.

**If you encounter a corrupted living document** (duplicate sections, contradictory entries, the same checklist repeated N times):
- Stop your current task.
- Prune to a single canonical form (use the most recent / most complete version of each duplicated section).
- Note the cleanup in your handoff note.
- File a `docs/decisions/OPEN_doc_drift_*.md` if you can't determine which version was canonical.

## Reproducibility contract

Every output is regenerable from the project's **verify command** (declared in the charter `## Stack` block) on a clean checkout. Nothing merges without it passing.

What "reproducible" means is set by the project's profile (see `profiles/`): e.g. byte-identical rebuild from raw for **data-science**; build + tests pass for **software-app**; source-traceability for **investigation**. For data profiles, builds are deterministic — pin dependencies, sort before writing, fix random seeds.

## Communication

Every agent writes a **handoff note** when completing a deliverable: `docs/handoffs/YYYY-MM-DD_{agent}.md`. Use [`templates/handoffs/YYYY-MM-DD_agent.template.md`](../templates/handoffs/YYYY-MM-DD_agent.template.md).

## Agent operating protocol

Every dispatch ticket must name the following before an agent starts:

- **Input checklist:** exact files, data, decisions, and handoffs the agent must read.
- **Output schema:** exact files, records, reports, or artifacts the agent must create or update.
- **Escalation triggers:** conditions that stop execution and require a decision request.
- **Allowed files:** paths the agent may edit for this dispatch.
- **Required validation command:** command, check, or inspection proving the output is usable.
- **Handoff template:** expected next-agent handoff note and recipient.

If any of these are missing, the agent asks the Orchestrator for a corrected dispatch instead of guessing.

## Escalation

Any agent blocked > one work session, or encountering a decision that changes shared conventions, escalates to the Orchestrator via a decision request in `docs/decisions/OPEN_*.md`.
