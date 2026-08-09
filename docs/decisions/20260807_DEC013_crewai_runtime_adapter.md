# DEC-013 — Establish the CrewAI runtime-adapter boundary and run-manifest contract

**Date:** 2026-08-07
**Authority:** Framework Architect / Orchestrator (with the user)
**Status:** Decided — Amendment A incorporated 2026-08-07

## Context

ChartworkAI governs long-lived project state; CrewAI executes agent workflows. T-018 was
originally framed as configuration export/ingest with run IDs, traces, and outputs recorded as
handoffs or decisions. That framing crosses the boundary established in DEC-005: it treats runtime
events as governance authority, risks persisting sensitive execution content, and would couple the
dependency-free ChartworkAI package to a fast-moving orchestration runtime.

CrewAI provides public synchronous and asynchronous kickoff APIs plus structured crew and task
outputs. Those surfaces are sufficient for a narrow adapter that records execution evidence without
turning ChartworkAI into an agent runtime.

## Ruling

1. The first runtime adapter will be a public Apache-2.0 reference implementation distributed
   independently as `chartworkai-crewai`, with import namespace `chartworkai_crewai`.
2. The core `chartworkai` distribution remains free of CrewAI and other runtime dependencies. The
   adapter depends only on `chartworkai`; CrewAI must not be a mandatory or optional package
   dependency until its vulnerable transitive ChromaDB chain is patched and independently verified.
   Users supply the CrewAI runtime they choose to operate.
3. The initial adapter supports local, non-streaming CrewAI `kickoff` and `akickoff` execution
   through guarded metadata, version, and capability checks against the user-supplied runtime. It
   does not implement CrewAI Flow, AMP, REST, webhooks, hosted tracing, streaming, configuration
   translation, memory, tools, or runtime orchestration.
4. Each attempted execution receives an adapter-owned `cwrun_<uuid4>` identifier and an immutable,
   schema-versioned manifest at
   `docs/integrations/crewai/runs/<run_id>.json`.
5. Manifest schema v1 records adapter and runtime versions, ChartworkAI project/phase/task
   references, public crew and task metadata, execution status and timing, usage, artifact metadata,
   capture policy, and capture-dependent output. Execution status is `succeeded`, `failed`, or
   `cancelled`. Artifact records contain only project-relative paths, SHA-256 hashes, byte sizes,
   and media types. Task output must come from the returned public execution output; the adapter
   must not fall back to `crew.tasks` for output capture.
6. Every manifest is validated against a JSON Schema shipped with the adapter before it is written.
   Writes must be project-confined, symlink-safe, collision-safe, crash-atomic, and no-replace: a
   partial write or colliding run ID must never expose or overwrite a manifest.
7. Capture defaults to `metadata`: identifiers, timings, input key names, formats, counts, usage,
   failure flags, and artifact hashes, with no execution content. `summary` requires a caller-supplied
   summarizer; `full` is an explicit opt-in. Recursive redaction and a bounded manifest size apply
   before serialization in every mode. Bounds are structural, covering nesting depth, collection
   sizes, task and artifact counts, string sizes, and total serialized bytes.
8. The adapter never persists input values, LLM messages, prompts, credentials, tool arguments,
   environment variables, trace payloads, or tracebacks. In `metadata` mode, a failed run records
   only the exception class and a SHA-256 digest of its message. `summary` and `full` may additionally
   record the redacted exception message, bounded to 2 KiB.
9. Handoff creation is optional and disabled by default. A caller requesting one must provide the
   governance producer and receiver explicitly; these identities are never inferred from CrewAI
   agents. Every handoff field and collection is bounded and validated before filing. A handoff may
   be filed only after a successful execution and manifest write and must reference the manifest and
   any recorded artifacts. Failed or cancelled executions produce manifests but no handoffs.
10. CrewAI runs and task completions are evidence, not decisions. The adapter must never call
    `file_decision`, infer authority, or update `PROJECT_CHARTER.md`, `STATUS.md`, or `TASKS.md`.
    A human or authorized project role files any resulting decision separately.
11. If CrewAI execution succeeds but governance recording fails, the adapter raises a distinct
    recording error that retains the CrewAI output. If execution fails, it records the failed
    manifest when possible and re-raises the original CrewAI exception.

## Amendment A — Dependency embargo and hardened capture contract

**Date:** 2026-08-07
**Authority:** Framework Architect
**Trigger:** A critical vulnerability was identified in CrewAI's transitive ChromaDB dependency
chain during implementation review.

Amendment A supersedes any earlier implication that `chartworkai-crewai` should declare or install
a CrewAI compatibility range. CrewAI remains user-supplied until the vulnerable dependency chain is
patched and independently cleared. The adapter's published metadata, wheel, and source distribution
must depend only on `chartworkai` and must contain no required or optional CrewAI or ChromaDB
dependency.

The release gate must also prove guarded runtime discovery, the three-state execution model,
metadata-safe failure recording, structural capture bounds, prohibition of `crew.tasks` output
fallback, crash-atomic no-replace publication, and bounded validated handoff inputs. Public adapter
documentation must disclose that CrewAI is user-supplied and explain the dependency embargo before
the adapter is released.

## Rationale

An independent reference adapter proves ChartworkAI's runtime-neutral governance model without
weakening the lightweight core or duplicating CrewAI's execution and observability responsibilities.
Metadata-first capture gives projects durable provenance while reducing accidental disclosure of
prompts, credentials, and tool output. Explicit handoff and decision boundaries preserve the
framework's authority model: automation may produce evidence, but it cannot grant itself decision
authority.

Publishing the first adapter under Apache-2.0 establishes a reusable integration pattern and lowers
adoption friction. Premium integrations may still be developed under DEC-004, but the reference
implementation remains part of the public ecosystem.

## Implementation notes

- The initial adapter release is versioned independently from ChartworkAI core. Runtime
  compatibility is detected without declaring CrewAI as a package dependency.
- The manifest JSON Schema ships with the adapter; the integration run directory remains optional
  and does not become a universal `framework.json` requirement.
- Optional handoffs use ChartworkAI's existing `file_handoff` API. The adapter has no decision-write
  capability.

## Consequences per agent

- **Orchestrator:** tracks T-018 as an integration deliverable and rejects any scope that converts
  runtime completion into project authority.
- **Framework Architect:** owns changes to the adapter boundary and manifest semantics.
- **Integrations Engineer:** implements `chartworkai-crewai` independently and confines changes to
  the adapter distribution and its documentation.
- **Dogfood & Compliance QA:** verifies sync/async success and failure, exception preservation,
  cancellation, capture modes, redaction, structural bounds, artifact safety, crash-atomic
  no-replace writes, optional handoffs, the absence of automatic decisions, guarded user-runtime
  compatibility, and the dependency embargo in all release artifacts.

## Related

- T-018, DEC-004, DEC-005, DEC-006, DEC-008.
