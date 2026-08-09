# ChartworkAI CrewAI Adapter

`chartworkai-crewai` records local CrewAI executions as durable ChartworkAI evidence. It wraps a
Crew's synchronous or asynchronous kickoff, writes an immutable schema-versioned run manifest, and
can file an explicit handoff after a successful run.

This is an independently buildable adapter with its own version and dependency range. It does not
add CrewAI or any other runtime dependency to the core `chartworkai` package.

The adapter itself depends only on `chartworkai`. It does not install CrewAI, ChromaDB, or a runtime
extra. The application supplies and secures its own compatible CrewAI installation. This boundary is
intentional while CVE-2026-45829 remains unresolved.

> **Publication status:** `chartworkai-crewai` is not yet published on PyPI. Install it from this
> repository until a separate adapter release is announced.

## Compatibility

- Python `>=3.10,<3.14`
- ChartworkAI `>=0.2,<0.3`
- User-supplied CrewAI `>=1.15.10,<1.16`
- Local, non-streaming `Crew.kickoff` and `Crew.akickoff`
- Linux and macOS filesystems that support descriptor-relative, no-follow opens and hard links

Windows support is not claimed for adapter `0.1.0`. The immutable-record guarantees require
filesystem primitives used to prevent symlink escapes and publish manifests atomically without
overwriting an existing record. The adapter fails closed when those primitives are unavailable.

The core `chartworkai` package remains dependency-free and supports its broader Python range. The
adapter's compatibility and releases are managed separately. Compatibility CI installs CrewAI
ephemerally at the declared range endpoints, but CrewAI is not part of adapter package metadata.

## Install From This Repository

First provide CrewAI in the application environment under your own dependency and security policy.
Then, from the repository root, install the adapter:

```bash
python -m pip install -e integrations/crewai
```

Installing the adapter does not install or upgrade CrewAI. Confirm that the environment already has
a supported runtime before calling `kickoff` or `akickoff`.

To build the adapter without building the core package:

```bash
python -m pip install build
python -m build integrations/crewai
```

## Record A Synchronous Run

```python
from chartworkai_crewai import CrewAIAdapter

adapter = CrewAIAdapter(project_root=".")
record = adapter.kickoff(
    crew,
    inputs={"topic": "retention policy"},
    task_refs=["T-018"],
)

print(record.run_id)
print(record.manifest_path)
```

Each attempted execution receives an adapter-owned ID such as `cwrun_<uuid>` and writes a validated
JSON manifest to:

```text
docs/integrations/crewai/runs/<run-id>.json
```

The adapter passes `inputs`, `input_files`, and `from_checkpoint` through to CrewAI unchanged.

## Record An Asynchronous Run

`akickoff` calls CrewAI's native asynchronous API:

```python
from chartworkai_crewai import CrewAIAdapter

adapter = CrewAIAdapter(project_root=".")
record = await adapter.akickoff(
    crew,
    inputs={"topic": "retention policy"},
    task_refs=["T-018"],
)
```

## Capture Policies

Capture is bounded to 256 KiB by default. If content must be removed to meet the limit, the manifest
sets `capture.truncated` and reports omitted records.

### Metadata

`metadata` is the default. It records identifiers, timing, input key names, task and failure counts,
usage, and artifact metadata. It does not store CrewAI output content.

```python
from chartworkai_crewai import CapturePolicy, CrewAIAdapter

adapter = CrewAIAdapter(
    project_root=".",
    capture=CapturePolicy(mode="metadata"),
)
```

### Summary

`summary` stores only the value returned by a caller-provided summarizer. The summarizer receives the
CrewAI output object; it must return a JSON-serializable value.

```python
adapter = CrewAIAdapter(
    project_root=".",
    capture=CapturePolicy(
        mode="summary",
        summarizer=lambda output: {"summary": output.raw[:500]},
    ),
)
```

### Full

`full` stores redacted Crew and task raw or structured outputs. It is always an explicit opt-in and
should be used only when the repository is approved to retain that content.

```python
adapter = CrewAIAdapter(
    project_root=".",
    capture=CapturePolicy(
        mode="full",
        redactor=my_project_redactor,
        redactor_id="project-policy-v2",
        max_bytes=128 * 1024,
    ),
)
```

Built-in recursive redaction runs before and after a custom redactor. It masks secret-like keys and
common bearer-token and API-key patterns, but pattern matching is not a substitute for reviewing the
data-retention policy and repository access controls.

The adapter does not directly read or serialize input values, LLM messages, prompts, credentials,
tool arguments, environment variables, or trace payloads. Only input key names are recorded.
Caller-generated summaries and full outputs can still echo sensitive source material, so review or
custom-redact them before enabling content capture.

## Artifact Integrity

Pass project-relative artifact paths to record their SHA-256 hash, byte size, media type, and relative
path. Artifact contents are not copied into the manifest.

```python
record = adapter.kickoff(
    crew,
    artifact_paths=["reports/final.md", "outputs/metrics.json"],
)
```

Artifacts must exist inside the project and must not traverse symlinks. Missing, external, or
symlinked artifacts are rejected. Absolute paths are never written to the manifest.

## Optional Explicit Handoffs

Handoffs are disabled by default. To file one, provide both governance identities explicitly; the
adapter never infers them from CrewAI agents.

```python
from chartworkai_crewai import HandoffSpec

record = adapter.kickoff(
    crew,
    artifact_paths=["reports/final.md"],
    handoff=HandoffSpec(
        agent="Research Crew",
        next_agent="Reviewer",
        produced="Research report",
        limitations="Source coverage is limited to the approved corpus.",
        verification="Review the manifest and compare the artifact hash.",
    ),
)
```

The handoff is written only after a successful execution and manifest write. It references the run
manifest and artifact hashes and discloses tool-failure counts. Failed runs never create handoffs.

CrewAI executions are evidence, not governance decisions. The adapter never files decisions or
updates `PROJECT_CHARTER.md`, `STATUS.md`, or `TASKS.md`; an authorized human or role must record any
resulting decision separately.

## Failure Semantics

- If CrewAI fails, the adapter attempts to write a failed manifest and then re-raises the original
  CrewAI exception. A recording problem is attached as an exception note when the Python version
  supports it.
- If CrewAI succeeds but manifest, artifact, or handoff recording fails, the adapter raises
  `RecordWriteError`. Its `output` attribute retains the successful CrewAI output, and
  `manifest_path` identifies a manifest already written before a later handoff failure.
- Manifests are immutable, collision-safe, atomic, and never overwritten.

```python
from chartworkai_crewai import RecordWriteError

try:
    record = adapter.kickoff(crew, artifact_paths=["reports/final.md"])
except RecordWriteError as exc:
    completed_output = exc.output
    existing_manifest = exc.manifest_path
    raise
```

## Non-Goals

The initial adapter does not support CrewAI Flow, AMP, REST, webhooks, hosted tracing, streaming,
`kickoff_for_each`, event-bus listeners, callback mutation, configuration translation, automatic
role mapping, raw trace ingestion, runtime orchestration, memory, tools, or hosting.

See [`DEC-013`](../../docs/decisions/20260807_DEC013_crewai_runtime_adapter.md) for the authoritative
runtime-adapter boundary and manifest contract.
