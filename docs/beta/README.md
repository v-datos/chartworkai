# ChartworkAI Concierge Beta

This directory is the operating record for T-021. The beta is a fixed-scope, paid,
14-day engagement for exactly three external design partners. Its purpose is to test
whether a real project can install, customize, and continue using ChartworkAI with a
reasonable amount of guided support.

## Completion gate

T-021 is complete only when `python scripts/check_beta_evidence.py` exits successfully.
That requires:

- exactly three external design partners;
- payment confirmed for each engagement;
- a clean ChartworkAI compliance result for each project;
- setup time measured consistently from installation start to the first clean check;
- one real governed action and one follow-up completed per partner; and
- explicit permission to publish at least one final case study.

Preparation, recruitment messages, scheduled calls, unpaid trials, or incomplete
records do not satisfy the gate.

## Standard engagement

- **Fee:** USD $300 per project plus applicable tax.
- **Service cap:** six total operator hours per project, including preparation,
  installation, support, and follow-up.
- **Preparation:** suitability screen, commercial terms, prerequisites, and privacy
  boundaries confirmed before the live session.
- **Installation session:** up to 90 minutes. The participant operates their own
  terminal while the ChartworkAI operator guides installation and customization.
- **Use period:** 14 days on a real, multi-session project.
- **Follow-up:** 30 minutes to review continued use, friction, and commercial value.
- **Deliverables:** initialized governance layer, clean compliance result, first
  governed action, and a de-identified outcome record.

Payment method, payment deadline, cancellation or refund terms, tax treatment, and
other jurisdiction-specific terms belong in a private written proposal. Do not put
financial or participant-identifying records in this public repository.

## Partner fit

Accept a partner only when all of these are true:

- they are independent of the ChartworkAI project and can give candid feedback;
- they have a real project expected to continue across multiple work sessions;
- the project has an existing Git repository and at least three roles or workstreams;
- they can install Python packages and commit repository changes;
- they experience a continuity, authority, decision, handoff, or reproducibility
  problem that ChartworkAI is designed to address; and
- the participant can approve the engagement or has identified the approver.

Defer single-session work, projects without a repository, requests for agent
orchestration or outsourced development, and engagements that require the operator to
handle credentials or unrestricted production access.

## Privacy boundary

The participant keeps control of their machine and repository. The operator does not
request or retain source code, credentials, personal contact details, payment data, or
production access. Recording is off by default and requires separate written consent.

Git contains only de-identified evidence files from `results/record.example.json`.
Signed agreements, invoices, consent records, contact details, raw notes, screenshots,
and repository identifiers stay in private owner-controlled storage. A private record
may be referenced by a non-identifying code such as `CONSENT-P001-01`; it is never
copied here.

## Commercial and privacy safeguards

This operator pack is not legal or tax advice. Confirm the rules that apply to the
owner and every partner before outreach or collection begins.

- For commercial email or text messages subject to Canada's Anti-Spam Legislation,
  document the consent basis and include the sender's identification, contact details,
  and a working unsubscribe method. See the
  [CRTC requirements](https://web.crtc.gc.ca/eng/internet/anti/reg.htm).
- Alberta private organizations should obtain appropriate consent, state the purpose,
  collect only what is reasonable, protect it, and destroy or anonymize it when no
  longer needed. See the
  [Alberta OIPC PIPA summary](https://oipc.ab.ca/resource/pipa-on-a-page/).
- Obtain written approval of any testimonial and permission to publish it before use.
  See the
  [Competition Bureau guidance](https://competition-bureau.canada.ca/en/deceptive-marketing-practices/types-deceptive-marketing-practices/use-tests-or-testimonials).

## Operating sequence

1. Use `recruitment.md` to invite and screen candidates.
2. Confirm the private commercial terms and collect payment before the session.
3. Run `session_runbook.md` without changing the timing definitions.
4. Complete the 14-day follow-up.
5. Create one de-identified JSON record per partner from
   `results/record.example.json`.
6. Use `case_study_permission.md` separately from participation and payment.
7. Run `python scripts/check_beta_evidence.py` and close T-021 only after it passes.
8. Publish only the case-study content and channels covered by the separate approval.

## Files

- `recruitment.md` - invitation and suitability screen.
- `session_runbook.md` - prerequisites, timing protocol, and follow-up.
- `case_study_permission.md` - separate publication-permission record.
- `results/README.md` - public evidence rules.
- `results/record.example.json` - schema example; never counted as evidence.
