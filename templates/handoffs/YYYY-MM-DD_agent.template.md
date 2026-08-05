# Handoff: {{Agent name}} — {{YYYY-MM-DD}}

**From:** {{Agent name and role}}
**To:** {{Next agent in chain}}
**Re:** {{One-line description of what was completed}}

---

## What was produced

- {{Deliverable 1}} — `{{path/to/file}}`
- {{Deliverable 2}} — `{{path/to/file}}`
- {{Updated artifact}} — `{{path/to/file}}` (was: {{prior state}}; now: {{new state}})

## Where it lives

{{Filesystem locations, parquet table names, branch / commit hashes if relevant. Be explicit enough that the next agent can find everything without guessing.}}

## What was decided along the way

- {{Any decision filed during this work — link to `docs/decisions/...`}}
- {{Any open question deferred — link to `docs/decisions/OPEN_...`}}

## Known limitations

{{Mandatory section. List the corners cut, the assumptions made, the data quirks not yet handled. Be honest — this is what the next agent needs to plan around.

If there are no known limitations, say so explicitly: "No known limitations." But this is rare.}}

- {{Limitation 1}}
- {{Limitation 2}}

## How to verify

{{Specific commands or checks the next agent (or QA) can run to confirm this work behaves as advertised.}}

```bash
{{verification commands}}
```

## Next agent in chain

**{{Next agent role}}** — should now {{action}}, consuming {{specific inputs from this handoff}}, producing {{expected next deliverable}}.

Suggested dispatch ticket:

> **Dispatch:** {{Next agent}}.
> **Inputs:** {{paths from this handoff}}.
> **Outputs:** {{expected new artifacts}}.
> **Done when:** {{criterion}}.
