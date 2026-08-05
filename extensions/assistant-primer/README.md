# Extension: assistant primer

Provide a repository orientation and onboarding guide for incoming AI assistants to prevent onboarding leaks, framework violations, and directory cruft. This packages the onboarding patterns and lessons identified across multiple implementations in the cross-project audit (e.g. preventing the assistant from leaving leftover files or ignoring the repository's build/test stack).

## Principles

- **Zero drift.** The primer contains clear declarations of the active roles, stack tools, and verify commands. A validation script cross-references these with `PROJECT_CHARTER.md` and `AGENTS.md` to guarantee they stay perfectly in sync.
- **Explicit boundaries.** Defines where code, tests, documentation, and data live, pointing the assistant directly to key entry points.
- **Rules of engagement.** Instructs the assistant on the framework's core rules (updating documents in-place, recording decisions, committing, and running compliance tests).

## Adopt it

1. Copy `assistant_primer.template.md` → `.ai-primer.md` in your project root.
2. Copy `verify_primer.sh` → your project's `scripts/` directory.
3. In your `PROJECT_CHARTER.md`'s `## Stack` block, append `scripts/verify_primer.sh` to your **Verify command**.
4. Customize `.ai-primer.md` to point to your project's specific entry point directories, and list its active agents/roles and stack commands.
5. Incoming AI assistants should read `.ai-primer.md` first to understand how to operate in the workspace.

## Files

- `assistant_primer.template.md` — the orientation document template (copy to `.ai-primer.md`).
- `verify_primer.sh` — the script that verifies the primer matches the charter and role specifications.
