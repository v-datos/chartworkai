# Decision: {{DQ-NNN}} — {{Short title}}

**Date:** {{YYYY-MM-DD}}
**Authority:** {{Agent role making the call — e.g., Domain Expert, Data Engineer, Orchestrator}}
**Status:** {{Open | Decided | Resolved | Superseded}}

---

## Context

{{What situation prompted this decision. Include:
- The data or evidence inspected (with counts where relevant).
- Why a choice is needed now.
- Which agents are affected by the outcome.

If quantitative — e.g., "1,012 of 1,023 station-year rows show sum(species) ≠ Total" — include a small table breaking down the discrepancy by category.}}

### Options considered

1. **Option A:** {{description}}. Pros: {{}}. Cons: {{}}.
2. **Option B:** {{description}}. Pros: {{}}. Cons: {{}}.
3. **Option C:** {{description}}. Pros: {{}}. Cons: {{}}.

---

## Ruling

**Ruling: Option {{X}} — {{one-sentence summary}}.**

{{Detailed statement of the ruling. Be precise enough that the implementer cannot reasonably misinterpret it. If the ruling has sub-rules (e.g., "use X in case A; use Y in case B"), enumerate them.}}

---

## Rationale

{{Why this option beats the alternatives. Cite evidence, domain reasoning, or precedent. If the decision involves a trade-off (e.g., simplicity vs. precision), name the trade-off and justify which side won.

Anticipate the reader six months from now who will ask "why did we do it this way?" — answer them.}}

---

## Implementation notes for {{owning agent}}

{{Concrete next steps. If a code change is needed, paste a code block showing the intended shape — even pseudocode is fine. Specify:

- Which files change.
- Which schemas update.
- Whether a rebuild is required.
- Whether existing parquet/output files become invalid.
- Whether tests need updating.
- Whether `docs/data/data_dictionary.md` or `docs/data/lineage.md` need entries.}}

```python
# Example implementation sketch (delete or replace)
{{code}}
```

---

## Consequences

- **For {{Producer}}:** {{e.g., must rebuild after merging this; new column added}}.
- **For {{Analyst}}:** {{e.g., new column available; old column retained but deprecated}}.
- **For {{Domain Expert}}:** {{e.g., interpretation note required in §X of report}}.
- **For QA:** {{e.g., new test required, schema validation will tighten}}.

---

## Related decisions

- Supersedes: {{DQ-NNN if any}}
- Related: {{DQ-NNN, DQ-NNN}}
- See also: {{file paths}}
