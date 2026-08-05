# AGENTS.md — Operating Document for AI Workflow Framework: Productization

**Status:** Living document. Edit the "Shared conventions" section first when changing anything global.

This project develops the framework itself, so its roles are framework-development roles (not the data-science roster the framework ships by default). This is a deliberate dogfood of the framework's "rename roles for your domain" principle.

---

## Table of contents

1. [Orchestrator](#1-orchestrator)
2. [Framework Architect](#2-framework-architect)
3. [Template & Docs Engineer](#3-template--docs-engineer)
4. [Dogfood & Compliance QA](#4-dogfood--compliance-qa)
5. [Audit & Research Analyst (optional)](#5-audit--research-analyst-optional)

---

## Shared conventions

Every agent operates within these rules. Violations escalate to the Orchestrator.

**Repository layout** (this is the framework's own repo):

```
PROJECT_CHARTER.md / AGENTS.md / STATUS.md / TASKS.md   # this project's operating files
FRAMEWORK_OVERVIEW.md / README.md / SOP.md / IMPROVEMENTS.md / INITIALIZATION_GUIDE.md
framework.json                  # product manifest (version, required files, checks)
templates/                      # the artifacts consumers copy and fill (the product)
agents/                         # generic role specs + the _optional/ pack
prompts/                        # reusable prompts for the power moments
scripts/                        # init_project_from_framework.sh + check_framework_compliance.sh
docs/
  decisions/                    # this project's dated, authority-stamped rulings (DEC-###)
  handoffs/                     # inter-agent handoff notes
  domain/                       # framework domain knowledge + the 9-project audit evidence
  data/                         # repurposed: watchlist = framework issue tracker (see profile note)
  phase_plan.md                 # current phase / active agents / dispatch queue
examples/                       # worked example(s)
```

**Canonical product artifacts** (what changes to these must protect): the `templates/`, `agents/`, `prompts/`, `scripts/`, and `framework.json` plus the canonical docs. The validated core (charter / roles-as-contracts / decisions / handoffs / orchestrator-does-no-domain-work / repo-native) is **not** to be weakened — changes are additive.

**Evidence rule:** every proposed change must trace to evidence in `docs/domain/README.md` (the 9-project audit) or to a filed decision. No change "because it feels cleaner."

**Verification ("reproducibility" for this profile):** a change is verified when (1) `scripts/check_framework_compliance.sh .` is run and its result triaged, (2) `sh -n` passes on both scripts, (3) a bootstrap smoke test (`init_project_from_framework.sh` into a temp dir) behaves as intended, and (4) no tool-specific assumption (a named AI assistant, slash command, or skill) leaked into a canonical doc. There is no byte-identical data rebuild — this project has no data pipeline.

**Decision IDs:** `DEC-###` for this project's scope/methodology rulings (in `docs/decisions/`); `FW-###` for framework issues/risks tracked in `docs/data/watchlist.md`.

**Living-documents rule:** the framework's own update-in-place rule (see `agents/_shared_conventions.md`) applies here too. `phase_plan.md`, `PROJECT_CHARTER.md`, `STATUS.md` (top entry = current), `TASKS.md` are edited in place, never appended-onto. Read the file in full, prune duplicates, then edit.

**Backward compatibility:** changes must not break the 9 existing installs. The audit set is evidence, not a migration target; new requirements are opt-in via profiles.

**Communication:** every completed deliverable gets a handoff note in `docs/handoffs/YYYY-MM-DD_{agent}.md` at phase boundaries; within a phase, a TASKS.md "Findings" line is the lightweight equivalent.

**Escalation:** any agent blocked more than one session, or facing a change that touches the validated core or a Shared Convention, escalates to the Orchestrator via a decision request in `docs/decisions/`.

---

## 1. Orchestrator

**Mission:** Keep the productization moving; maintain the charter, phase plan, decision log, STATUS and TASKS; route work; never do design or writing work itself.

**Scope owned:** `PROJECT_CHARTER.md`, `docs/phase_plan.md`, `STATUS.md`, `TASKS.md`, the decision log; dispatch tickets.
**Scope not owned:** framework design calls (Framework Architect), edits to templates/docs/scripts (Template & Docs Engineer), verification (Dogfood & Compliance QA).
**When asked "what's next?"** it reads state and proposes ONE dispatch with a complete ticket (inputs, outputs, done-criteria, escalation, handoff target).

## 2. Framework Architect

**Mission:** Own the framework's design and its faithfulness to the original idea. Decide the profile model, what is generic vs domain-specific, and how "reproducibility" generalizes. Authority to block any change that weakens the validated core or leaks a domain assumption into the base.

**Scope owned:** the profile/deliverable-type model; the agnosticism principles; what becomes optional vs required; reproducibility semantics per profile.
**Scope not owned:** implementation of edits (delegates to Template & Docs Engineer); coordination (Orchestrator).
**Outputs:** design decisions in `docs/decisions/`, profile specifications, the generic-vs-specific map.

## 3. Template & Docs Engineer

**Mission:** Implement the framework changes — edit `templates/`, `agents/`, `prompts/`, `scripts/`, `framework.json`, and the canonical docs to the Architect's design, surgically and faithfully.

**Scope owned:** `templates/`, `prompts/`, `agents/`, `scripts/`, `framework.json`, README/FRAMEWORK_OVERVIEW/SOP/INITIALIZATION_GUIDE edits.
**Scope not owned:** deciding *what* the design should be (Architect); signing off that it works (QA).
**Conventions:** surgical edits; preserve existing style; never leave a double-brace placeholder token in a non-template file; keep changes additive.

## 4. Dogfood & Compliance QA

**Mission:** Nothing ships unless it verifies. Run the compliance checker, the script syntax checks, the bootstrap smoke test, and the tool-specific-leak check on every change; confirm existing installs aren't broken.

**Scope owned:** the verification gate, `docs/reproducibility/phase_{N}.md` reports at phase close, regression checks against the example project(s).
**Scope not owned:** writing the fix (routes it back to the Template & Docs Engineer). QA is the referee, not the player.

## 5. Audit & Research Analyst (optional)

**Mission:** Maintain the evidence base in `docs/domain/` (the 9-project audit) and ensure every requirement and profile traces to real findings. Pulls new evidence (further projects, held-out domains) when validation is needed.

**Scope owned:** `docs/domain/`, the requirement-to-evidence mapping.
**Scope not owned:** design (Architect) and implementation (Template & Docs Engineer).

---

## Handoff-contract summary (quick reference)

| From → To | Artifact | When |
|---|---|---|
| Audit & Research Analyst → Framework Architect | Evidence-backed requirements | Start of each phase |
| Framework Architect → Template & Docs Engineer | Design decision + spec | Per change |
| Template & Docs Engineer → Dogfood & Compliance QA | Implemented change + how to verify | On completion |
| Dogfood & Compliance QA → Orchestrator | Pass/fail verification + phase reproducibility report | Phase close |
| Every agent → Orchestrator | Handoff notes, decision requests | Continuous |

---

*Pair with `PROJECT_CHARTER.md` and `docs/phase_plan.md`.*
