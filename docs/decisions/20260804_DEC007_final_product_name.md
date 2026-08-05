# DEC-007 — Final public name is ChartworkAI

**Date:** 2026-08-04
**Authority:** Orchestrator (with the user)
**Status:** Decided
**Amends:** DEC-005

## Context

DEC-005 renamed the product to **Chartwork**. Before publication, an alternative spelling — *ChatworkAI* — was proposed. A name-clearance check found two problems with it:

1. **An existing mark.** [Chatwork](https://go.chatwork.com/en/) is a live business-chat product operated by kubell (formerly Chatwork Co., Ltd.), used by 206,000+ companies across 180+ countries, with active pricing and enterprise customers. Both products are B2B collaboration software, so the goods and services overlap directly, and an "AI" suffix is a weak distinguisher.
2. **It contradicts the product's thesis.** ChartworkAI's central claim is that all coordination state lives in version-controlled Markdown, **never in chat**. A name built on "chat" argues against the thing being sold, and it discards the `chart` → `PROJECT_CHARTER.md` tie that motivated the original choice.

Registry availability was not the constraint: `chatworkai`, `chartworkai`, and `chartwork` were all free on PyPI and npm at the time of checking.

## Ruling

The public product name is **ChartworkAI**, distributed as `chartworkai` on PyPI with `chartworkai` as the CLI command and the Python package name. The MCP server and its four tools are named to match (`chartworkai_check`, `chartworkai_state`, `chartworkai_file_decision`, `chartworkai_file_handoff`).

DEC-005 stands as the record of the rename away from "AI Workflow Framework"; this decision only fixes the final spelling.

## Rationale

Keeping the "chart" root preserves both the trademark distance from Chatwork and the semantic tie to the charter — the artifact the whole method is built on. The "AI" suffix was added for discoverability in the agent-tooling category.

## Implementation notes

- `src/chartwork/` → `src/chartworkai/`; 24 files rewritten; `pyproject.toml` name, entry point, and wheel path updated.
- `docs/decisions/20260804_DEC005_chartwork_rename.md` keeps its original filename and content: it is a historical record of what was decided at the time, and rewriting it would be the exact revisionism this decision log exists to prevent.
- **Defensive registration:** `chartwork` (without the suffix) remains unclaimed on PyPI and should be registered as an alias pointing at `chartworkai` before launch, to stop a squatter taking the obvious near-miss of our own name.

## Consequences per agent

- **Release & Compliance Engineer:** publish as `chartworkai`; register `chartwork` defensively; a professional trademark clearance search is still advisable before any commercial launch.
- **Docs & GTM Engineer:** the canonical line is *"Agent frameworks orchestrate. ChartworkAI governs."*

## Related

- DEC-005 (rename and repositioning), DEC-006 (Apache 2.0), DEC-004 (open-core model).
