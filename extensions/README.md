# Extensions

Optional, templated modules a project can adopt for needs the framework's core doesn't cover. Each is opt-in, has a clear home **outside** the canonical operating docs, and is tool-/tracker-agnostic where possible. Adopt one by copying its template(s) into your project as its own README describes.

Each extension traces to ≥2 real implementations (see the cross-project audit in a project's `docs/domain/`).

| Extension | What it adds | Status |
|---|---|---|
| [`external-tracker-sync/`](external-tracker-sync/) | Mirror `TASKS.md` / `STATUS.md` to an external tracker (ClickUp / Linear / Notion / …) for stakeholder visibility | available |
| [`claims-gate/`](claims-gate/) | A staging table + evidence-tier promotion for investigative / knowledge-base projects | available |
| [`experiment-log/`](experiment-log/) | A templated experiment / run tracker for competition / ML projects | available |
| [`assistant-primer/`](assistant-primer/) | A short orientation doc (repo layout, entry points, conventions) for the AI assistant | available |

**Rule:** an extension never changes the meaning of the canonical operating docs. Its instructions and config live in the extension's own home (e.g. `docs/integrations/`), **never pasted into `AGENTS.md` or `PROJECT_CHARTER.md`**.
