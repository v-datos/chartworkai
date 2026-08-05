# Profile: investigation

**Deliverable:** evidence-backed findings — a report, a knowledge base, a public dataset of claims — where the work is judged on whether each assertion holds up, not on whether a pipeline runs.
**Declare:** add `**Profile:** investigation` near the top of `PROJECT_CHARTER.md`.

## Required artifacts

Universal only. **The `docs/data/` contract triad is NOT required.** If your investigation also publishes a curated dataset as a product in its own right, use the `database` profile for that work instead of bolting contracts onto this one.

Adopt the **`claims-gate` extension** (`extensions/claims-gate/`). It is the defining artifact of this profile.

## Reproducibility / verify

"Reproducible" = **every published claim traces to an archived source at a stated evidence tier**. There is no rebuild to run; the verification is that nothing reached the findings without passing the gate.

Claims enter a staging ledger and are only promoted when they meet the tier bar:

| Tier | Meaning |
|---|---|
| E1 | Primary document, archived locally (court filing, contract, registry entry) |
| E2 | Named on-record source, or a second independent primary |
| E3 | Credible secondary reporting, attributed |
| E4 | Single unverified source — may inform direction, never publishable |
| E5 | Rumour — recorded so it is not rediscovered, never promoted |

Declare a verify command in `## Stack` that runs the gate check: no `Promoted` claim may sit below your publication threshold, and none may carry a dead or missing source link. **Archive the source, don't just link it** — the web decays faster than an investigation closes.

## Default roles

Orchestrator · Domain Expert (the lead investigator or editor — owns whether a claim is supportable) · Producer (researcher / data gatherer) · **Fact-checker** as a distinct role from whoever wrote the claim · QA.

The separation matters more here than anywhere else in the framework: the author of a claim is the worst possible judge of whether it clears the bar.

## Layout emphasis

`docs/investigation/claims_gate.md` for the ledger, an archive directory for retrieved sources (with retrieval dates), `docs/domain/` for the entity and terminology definitions that keep two researchers from meaning different things by the same name.

## Notes on language and jurisdiction

Investigations are frequently conducted in the subject's language. Write your content in whatever language fits — only the structural labels the checker reads must stay English (see `PORTABILITY.md`). Where publication carries legal exposure, record the review as a decision with a named authority; that record is the thing that will be asked for.

## Evidence

A Spanish-language corruption investigation, whose staging-and-promotion pattern the `claims-gate` extension was extracted from, and where the gate caught a headline figure that was wrong by a factor of four ($25B → $5.55B) before publication. This is the one profile currently grounded in a **single** implementation rather than two; it is included because that implementation produced the framework's most transferable pattern, but the design should be revisited against a second investigation before it is treated as settled.
