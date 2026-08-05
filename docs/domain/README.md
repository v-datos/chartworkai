# Domain Knowledge — what this framework is, and what the field taught us

This is the evidence base for the framework's productization. It records the framework's own principles plus the findings from auditing 9 real implementations on 2026-06-07.

## The framework, in one breath

A **repo-native operating system for long, complex, multi-agent AI projects**: all coordination state lives as version-controlled Markdown (never chat), so any session reconstructs full project state from the repo. Its validated core: a **charter** (single source of truth), **roles-as-contracts** (spec + system prompt, explicit "owns / doesn't own"), **decisions** as dated authority-stamped artifacts, **handoffs** as the inter-agent currency, an **Orchestrator** that routes but does no domain work, a **living-documents** update-in-place rule, and a **compliance checker** that defines "installed."

## The audit set (9 implementations)

| Project | Domain · stack · assistant | Fit | Lesson |
|---|---|---|---|
| a marine-ecology research project | marine-ecology research · Python · Claude | native baseline | decision-authority corrected/demoted 6 results pre-publication; auto-generates phase_plan via a session-end hook |
| a sports-betting analytics platform | betting platform · Python · Claude(+Codex) | good | a decision blocked deploying uncalibrated models; "byte-identical rebuild" impossible with live APIs |
| a bird-audio classification competition | bird-audio ML comp · Python+GCP · Claude | good | cloud training makes data/ + reproduce hollow; scaffold left; decisions unlinked from charter |
| a tabular ML competition entry | Kaggle tabular ML · Python · — | good | a competition's deliverable is experiment-log + submission, not a report; handoffs collapsed |
| a motorsport strategy analysis | F1 strategy · Python · **Qwen** | good | plain-Markdown contracts survived an assistant swap with zero Claude-erosion |
| a national waste-to-energy database | curated database · Python · Claude(+Kimi) | good | data-contract triad is the best-fit asset for DBs; decision log under-used (2/9 phases) |
| a geospatial detection service | geo-detection + deployed app · Python+web · Claude | **strained** | no slot for deployed services/devops/frontend; phase_plan froze at install |
| a Node/TypeScript trip-planning web app | **Node/TS web, zero Python** · Claude | good | the checker is already agnostic (27/27); friction is all in prose |
| a Spanish-language corruption investigation | investigative DB+dashboard · Py+web · **Claude+Codex, Spanish** | good | the "claims gate" (evidence-tier promotion) is the killer pattern; i18n works if labels stay English |

## Cross-cutting patterns (requirements feed from these)

1. **Reproducibility must be pluggable** — "byte-identical rebuild from raw" broke in ~6/9 (live APIs, cloud training, deployed services, web builds, journalism). → FW-005 / Phase 1 B.
2. **Deliverable type is unmodeled** — report / database / competition / app / investigation / deployed each want different layouts, artifacts, roles. → FW-006 / Phase 1 A.
3. **The decision log is the differentiator** — demonstrably prevented bad deployments and corrected published claims. IDs (DQ-/SC-/MD-) mostly dropped though. → Phase 2 G.
4. **Living documents decay predictably** — phase_plan freezes/goes stale; STATUS bloats or freezes. the marine-research project's generate-from-state hook is the cure. → FW-007 / Phase 2 F.
5. **Handoffs are conditional** — thrive with parallel agents (56, 67), collapse with one sequential agent. → Phase 2 H.
6. **Teams reinvent the same six extensions** — external-tracker sync (5/9), experiment-log, claims-gate, milestone-repro (3/9), prereg-plan, assistant-primer. → FW-008 / Phase 2 E.
7. **Onboarding leaks** — `_framework_*` cleanup skipped (2/9); no stack declaration; i18n + multi-assistant + tool-leak undocumented. → Phase 3 I.

## Generic core vs data-science-specific shell

- **Generic (keep as base):** charter, roles-as-contracts, decisions, handoffs, Orchestrator-no-domain-work, phase gating, the compliance checker's structural checks.
- **Data-science-specific (make optional via profiles):** `data/raw|processed` layout, the data-contract triad, "reproducibility = byte-identical rebuild," statistical vocabulary in agent specs, `reports/figures` + notebooks, the uv/ruff/mypy/pytest/Make toolchain.

## Sellability (verdict)

Not yet a turnkey product, but the core IP is validated across 9 domains and 3 assistants — a productizable methodology. Blockers and the path are the charter's phases (Tiers 1–3).
