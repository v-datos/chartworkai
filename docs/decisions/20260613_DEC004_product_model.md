# DEC-004 — Product model and go-to-market strategy

**Date:** 2026-06-13
**Authority:** Orchestrator
**Status:** Decided

## Context

Phase 3 is closing. We need to define the framework's product model and identify our first target buyer (resolving Open Questions OQ1 and OQ4).

## Ruling

1. **Product Model (OQ1):** Adopt an **open-core** model.
   - The core framework (including the CLI bootstrap installer `init_project_from_framework.sh`, the compliance checker linter `check_framework_compliance.sh`, the living-document generator `generate_phase_plan.sh`, and the base `data-science` and `software-app` templates) will be open source and free.
   - Advanced profiles (e.g., `deployed-service`, `database`) and premium extension packs (e.g., advanced integration templates, premium automated verification scripts) will be offered as paid add-ons.
2. **Target Buyer (OQ4):** Our primary go-to-market audience is **solo AI power-users, agile agencies, and software development teams** who rely heavily on AI coding assistants (such as Claude Code, Cursor, Qwen, etc.) and require robust, repository-native management practices to prevent scope drift and maintain reproducibility.

## Rationale

- **Open-Core:** Making the core linter and CLI free drives early adoption and developers' trust. Developers are more likely to integrate the framework into their workflows if they can inspect and run the linter locally for free.
- **Paid Profile/Extension Packs:** Developers and agencies are willing to pay for pre-configured, production-ready profiles and integrations (like Linear/ClickUp synchronization, automated claims promotion, and deployment scripts) that save direct engineering hours.
- **Target Audience:** Solo power-users and small agencies experience the highest pain when managing long-lived agent interactions (where context window drift frequently causes agents to forget previous decisions, duplicate documentation sections, or leak tool-specific assumptions).

## Implementation notes (shipped this session)

- Documented this model in `docs/decisions/20260613_DEC004_product_model.md`.
- Linked this decision in `PROJECT_CHARTER.md` and marked OQ1 and OQ4 as resolved.
- Neutralized tool-specific leaks across all core files to support the multi-assistant positioning.

## Consequences per agent

- **Template & Docs Engineer:** Maintain the open-core structure in the main repository, keeping the main templates and scripts cleanly separated from optional premium packages.
- **Dogfood & Compliance QA:** Verify that the open-source CLI and compliance linter install and run cleanly on clean systems without external or proprietary dependencies.

## Related

- DEC-002 (profile model).
- DEC-003 (Phase 1 direction).
