# Profile: deployed-service

**Deliverable:** a running service and the infrastructure that keeps it running. The work is not done when the code is merged; it is done when the thing is live and can be rolled back.
**Declare:** add `**Profile:** deployed-service` near the top of `PROJECT_CHARTER.md`.

## Required artifacts

Universal only. **The `docs/data/` contract triad is NOT required.** If the service is backed by a dataset you also publish, govern that separately under the `database` profile.

## Reproducibility / verify

"Reproducible" = **a running release is traceable back to source**. Declare a verify command in `## Stack` that covers build *and* deployment:

- the build passes tests and produces an artifact,
- the release is identified by **config + image digest + job/run URI**, all traceable to a commit,
- a **rollback has been tested**, not merely documented.

If you cannot reproduce what is currently running from source, that is the first thing to fix — everything else in the governance layer is describing a system nobody can account for.

**Secrets never enter git.** Credentials come from the environment or a secret store, and a secret scan runs before every release. This profile is the one most likely to tempt someone into committing a service-account key.

## Default roles

Orchestrator · Domain Expert (product owner) · Software Engineer · **Frontend Engineer** (if there is a UI) · **Deployment Engineer** · QA. The last two are in `agents/_optional/` and exist because of this profile: the audit found deployed-app projects had no slot for devops or frontend work, so it was crammed into the Orchestrator — which breaks the framework's central rule that the Orchestrator does no domain work.

## Layout emphasis

Your stack's idiomatic source tree, plus deployment config (Dockerfile, hosting config, pipeline definitions) and a release runbook. `docs/reproducibility/phase_{N}.md` records what was verified at each phase close, including which release was live.

## Watch for

This profile decays fastest. The audit found one deployed-app project whose `phase_plan.md` froze at Phase 1 while the work had reached Phase 6 — shipping pressure crowds out the plan. Regenerate it from state (`chartworkai plan`) rather than hand-editing, and let the staleness check tell you when it has drifted.

## Evidence

A geospatial detection service deployed on Firebase — the project that exposed the missing devops and frontend roles — and a Node/TypeScript trip-planning web app with a server and build pipeline, containing no Python at all. See the cross-project audit in `docs/domain/README.md`.
