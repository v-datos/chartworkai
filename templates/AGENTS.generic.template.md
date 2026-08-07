# AGENTS.md - Operating Document for {{PROJECT_NAME}}

**Status:** Living document. Update shared conventions before changing a rule that applies to
every role.

**Profile roles:** {{DEFAULT_ROLE_LIST}}

## Shared conventions

Every agent operates within these rules. Violations escalate to the Orchestrator.

**Repository layout:** Define the project-owned paths and ownership boundaries here. The generic
profile imposes no source-code, data, report, or deployment layout.

**Canonical artifacts:** List the files, records, services, or outputs every role must treat as
authoritative.

**Tooling:** Declared in the charter `## Stack` block.

**Validation contract:** Every deliverable names a validation command or review procedure. No
phase closes until the declared validation passes.

**Communication:** Every completed deliverable gets a handoff note identifying what was produced,
where it lives, known limitations, validation evidence, and the next role.

**Escalation:** Any role blocked for more than one work session, or facing a change to scope or a
shared convention, files a decision request for the Orchestrator.

**Agent operating protocol:** Every dispatch ticket names its inputs, output schema, escalation
triggers, allowed files, required validation, and handoff recipient.

## Orchestrator

Coordinates the project, maintains operating state, routes work, and records decisions. The
Orchestrator does not perform specialist work or override domain authorities.

## Project roles

Create one section for each profile role listed above. For every role, define:

- Mission and scope owned
- Inputs and required reading
- Outputs and allowed files
- Escalation triggers
- Required validation command
- Handoff target

## Handoff contract

Every role hands completed work to the next named role through a dated file in `docs/handoffs/`.
The receiving role must be able to resume from repository artifacts without relying on chat history.
