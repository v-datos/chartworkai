# Extension: external-tracker sync

Mirror the repo's `TASKS.md` and `STATUS.md` to an external project tracker (ClickUp, Linear, Notion, Jira, Asana, …) so stakeholders who don't read the repo can follow progress. Five of nine audited projects bolted this on by hand — this packages it.

## Principles

- **The repo is the source of truth.** `TASKS.md` / `STATUS.md` are canonical; the tracker is a **one-way, read-only mirror** (repo → tracker). Never sync tracker → repo — that reintroduces the chat-drift the framework exists to prevent.
- **Home: `docs/integrations/`, never `AGENTS.md`.** Integration instructions and config live in `docs/integrations/<tracker>.md`. Do not paste them into the agent-spec or the charter — one audited project did, and it contaminated `AGENTS.md`.
- **Tracker- and assistant-agnostic.** The sync script targets a configurable endpoint/command; wire the trigger via whatever your assistant or toolchain supports — not a hard-coded one.
- **No secrets in git.** The tracker API token comes from the environment / a secret store.

## Adopt it

1. Copy `integration.template.md` → `docs/integrations/<tracker>.md` and fill it in (which tracker, what's mirrored, the trigger, where the token comes from).
2. Copy `sync_tracker.sh` → your project's `scripts/` and implement the one `push_to_tracker` function for your tracker's API.
3. Choose a trigger:
   - **Manual:** run `scripts/sync_tracker.sh` after editing TASKS/STATUS.
   - **Hooked:** run it on edits to `TASKS.md` / `STATUS.md` via your assistant's hook mechanism (e.g. a Claude Code `PostToolUse` hook in `.claude/settings.json`, a `.codex` hook, or a git `pre-commit` hook). Keep the hook in the assistant's own config — see [`../../PORTABILITY.md`](../../PORTABILITY.md).

## Files

- `integration.template.md` — the per-project integration doc (copy to `docs/integrations/`).
- `sync_tracker.sh` — a tracker-agnostic reference sync script (copy to `scripts/`; fill in the API call).
