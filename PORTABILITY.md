# Portability — any stack, any AI assistant, any language

The framework's coordination layer is plain Markdown + POSIX shell, so it travels across tech stacks, AI assistants, and human languages. This note records how — each point is backed by a real implementation (see `docs/` audit evidence in projects built with the framework).

## Any tech stack

The base templates carry no language assumptions. Declare yours in the charter `## Stack` block (language/runtime, package manager, build/test/**verify** commands) and pick a `Profile:` (see `profiles/`). The compliance checker enforces only **structure** — files present, no unresolved placeholders, TASKS shape, phase↔charter sync, decisions linked — never a specific language or toolchain. Evidence: a Node/TypeScript project with zero Python passes cleanly, with no data contracts (it runs the `software-app` profile).

## Any AI assistant

The canonical artifacts (`PROJECT_CHARTER.md`, `AGENTS.md`, decisions, handoffs) are paste-ready plain Markdown and run unchanged under Claude Code, Qwen, Codex, etc. Two rules keep them portable:

- **No tool-specific syntax in canonical docs.** Don't embed an assistant's slash commands, "skills", or config (e.g. a `/read` or a named skill) in `AGENTS.md` or the charter — they silently no-op under a different assistant. Keep such things in that assistant's own config dir (`.claude/`, `.qwen/`, `.codex/`), gitignored or clearly assistant-scoped.
- **Record the assistant choice as a decision** when it matters (e.g. "this project runs under Qwen; `AGENTS.md` is assistant-agnostic by design").
- **Multi-assistant routing:** if you delegate a phase to a second assistant, give it a brief in `docs/handoffs/` (or `docs/delegation/`) and apply the same verify/QA gate to its output — delegated phases still owe a reproducibility report at phase close.

Evidence: a project ran end-to-end under **Qwen** with zero Claude-specific erosion in its canonical docs; another routed data-heavy phases to **Codex** alongside Claude.

## Any language / locale

Author content in any language. Keep only the **structural labels the checker reads in English** so enforcement still works:

- `## In Progress` (the section header in `TASKS.md`)
- the `Current phase:` line and `Phase N` references (`docs/phase_plan.md` / charter)
- the `Profile:` line (charter)

Everything else — narrative, domain docs, case files, reports — can be in your language. Evidence: a Spanish-authored investigation passed compliance by keeping those few labels English while writing all content in Spanish.
