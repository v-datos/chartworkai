# Concierge Beta Session Runbook

Use the same procedure for all three partners so setup times and outcomes are
comparable.

## Before the session

- Confirm written scope, fee, payment, cancellation terms, and included support.
- Confirm that the partner meets every fit criterion in `README.md`.
- Confirm Python 3.9 or newer, `pip`, Git, repository access, and permission to
  change the repository.
- Ask the participant to create a branch or backup according to their own policy.
- Agree that the participant controls the terminal and reviews every write.
- Confirm that credentials, source code, personal data, and payment data will not be
  copied into session notes or the public evidence record.
- Keep recording off unless separate written recording consent exists.
- Open a private timer record using the partner code only.

## Timing definitions

- **T0 - install start:** immediately before the participant runs the package
  installation command.
- **T1 - scaffold created:** when `chartworkai init` finishes successfully.
- **T2 - first clean check:** when `chartworkai check . --strict` first exits zero
  after the project documents are customized.
- **T3 - governance commit:** when the initialized governance layer is committed to
  the partner repository.
- **Setup seconds:** elapsed monotonic-clock seconds from T0 to T2.
- **Setup minutes:** setup seconds divided by 60 and rounded up. Pauses caused by
  unrelated interruptions remain included; note them as an intervention code.

T2 is the common completion point used by the evidence checker. T0, T1, T2, and T3
wall-clock times are private diagnostic measures. The public record contains only the
installation date, elapsed setup seconds, and calculated setup minutes.

## Installation session

### Baseline - 10 minutes

1. Restate the project's deliverable, current phase, roles, and pain point.
2. Agree on one real task that will become the first governed action.
3. Record T0 and start the participant's installation.

### Install and initialize - 15 minutes

```bash
python -m pip install chartworkai
chartworkai --version
chartworkai init . --name "Project Name"
```

Use a built-in preset only when it genuinely fits. Otherwise use the generic core
or a reviewed project-owned profile. Record T1 when initialization completes.

### Customize and verify - 45 minutes

1. Replace the scaffold placeholders in `PROJECT_CHARTER.md` and `AGENTS.md`.
2. Confirm roles, authority boundaries, current phase, tasks, and validation command.
3. Remove temporary `_framework_*` reference directories after customization.
4. Run the strict check and resolve findings:

```bash
chartworkai check . --strict
```

Record T2 at the first zero exit and capture monotonic elapsed seconds from T0 to T2.

### Activate and commit - 15 minutes

1. Record one real governed action: a task dispatch, decision, handoff, or state
   review that changes how the project will proceed.
2. Review the generated documents before committing them.
3. Commit according to the partner's normal Git process and record T3.

### Debrief - 5 minutes

Capture only de-identified friction codes, operator interventions, the partner's
expected outcome, and the scheduled follow-up. Do not request case-study permission
during troubleshooting or make support conditional on permission.

## Intervention codes

- `ENV` - Python, package installation, shell, or path issue.
- `FIT` - selecting generic, a preset, or a project-owned profile.
- `DOC` - understanding or customizing a governance document.
- `CHK` - understanding or resolving a compliance finding.
- `GIT` - branch, ignore, diff, or commit workflow.
- `SEC` - privacy or security boundary required a change.
- `INT` - unrelated interruption included in elapsed setup time.
- `OTHER` - non-sensitive issue described only in private notes.

## Day-14 follow-up

1. Confirm whether the governance layer remains in the repository.
2. Confirm whether at least one task, decision, or handoff was updated after the
   installation session.
3. Ask what was used, ignored, confusing, or missing.
4. Ask whether the partner would continue using or paying for the product and why.
5. Record the follow-up date, continued-use result, and de-identified friction codes.
6. Offer the separate case-study permission process. Participation and support are
   complete even if permission is declined.
7. Create the public-safe JSON evidence record and run the evidence checker.
