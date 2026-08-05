# DEC-005 — Rename to Chartwork; reposition as the governance layer; ship a Python package

**Date:** 2026-08-04
**Authority:** Orchestrator (with the user)
**Status:** Decided

## Context

A competitive review against **CrewAI** (v1.15.10 — 56.6k GitHub stars, ~13.3M PyPI downloads/month, $18M raised) plus a second independent assessment converged on the same conclusion: CrewAI and this framework are **not competitors**. CrewAI is a runtime orchestration library that executes agents; this framework is a governance layer that keeps long-lived human+AI projects coherent.

Critically, CrewAI's own documentation has **no concept** of a project charter, human-authored decision records, phase gating, decision provenance, or reproducibility — its entire persistence surface (memory, flow state, checkpoints, traces) is execution-scoped instrumentation for machines resuming, not governance for humans. This is a documented, unmet need: a community thread asking how to handle auditability and governance in production CrewAI deployments was auto-closed after 30 days with zero replies, and an analyst assessment concluded *"CrewAI orchestrates. Something else has to certify what your agents are reasoning over."*

Two naming constraints forced the issue: the acronym "AIWF" is not marketable, and **`aiwf` is already taken on PyPI**.

## Ruling

1. **Rename the product to `Chartwork`.** "Chartwork" is the nautical discipline of plotting and *recording* a vessel's course — and it contains "chart", tying directly to `PROJECT_CHARTER.md`, the framework's primary artifact. Verified available on PyPI.
2. **Reposition** from "a multi-agent project framework" to **"the governance layer for agentic work."** Canonical line: *"Agent frameworks orchestrate. Chartwork governs. Charter, decisions, handoffs, and phase gates that survive across sessions, assistants, and months — works with CrewAI, LangGraph, Claude Code, Cursor, or plain humans."* Do not compete head-on with runtimes; treat them as distribution channels.
3. **Ship a Python package** (`pip install chartwork`) wrapping the proven Markdown file contracts, starting with `chartwork check` (the compliance linter) with `--json` output. **Zero runtime dependencies** — Chartwork governs projects in any language and must never impose a dependency tree on the repo it audits.
4. **Markdown remains the durable public contract.** The Python package parses and validates those contracts; it does not replace them. Chartwork will not build LLM adapters, agent loops, tool execution, memory, or hosting — those runtimes already own that surface.

## Rationale

The core IP (charter, roles-as-contracts, authority-stamped decisions, file-based handoffs, phase gates) is validated across 9 real implementations, 3 AI assistants, and 2 human languages, with hard evidence of prevented harm — a decision record blocked deploying uncalibrated models, another demoted an unsupported causal claim before publication. That value is real but was trapped in a methodology; a methodology is hard to sell, whereas a linter that runs in CI and an MCP server that any assistant can call are products.

## Implementation notes (this session)

- Scaffolded `pyproject.toml` + `src/chartwork/` (`models.py`, `checks.py`, `cli.py`), zero runtime deps, Python ≥3.9.
- Ported all 16 checks from `scripts/check_framework_compliance.sh`. **Verified parity:** exit codes agree with the shell across 8 differential scenarios, including the absolute-path false-positive and `non-data-science` profile regressions.
- Two deliberate divergences, documented in `checks.py`: the placeholder scan now prunes **every** `_framework_*` directory (the shell pruned only 3, double-reporting one root cause), and the STATUS date parses from any `## YYYY-MM-DD` heading.
- Fixed two confirmed release defects: the installer did not ship `generate_phase_plan.sh` to consumers although the implementation guide told them to run it; and that generator used `cut -d'—'`, which fails with "bad delimiter" on the multibyte em dash and silently blanked every decision ID/topic.

## Consequences per agent

- **Template & Docs Engineer:** rename across public docs; keep Markdown contracts stable.
- **Dogfood & Compliance QA:** both the shell checker and `chartwork check` must stay green on this repo; parity is a release gate until the shell is retired.
- **Framework Architect:** the Python API is now a public surface subject to semantic versioning.

## Related

- DEC-004 (open-core product model — unchanged; Chartwork is the free core).
- DEC-002 (profile model), DEC-003 (Phase 1 direction).
