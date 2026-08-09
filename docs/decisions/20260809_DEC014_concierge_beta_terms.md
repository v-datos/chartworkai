# DEC-014 — Set the T-021 concierge beta commercial terms

**Date:** 2026-08-09
**Authority:** Orchestrator (with the user)
**Status:** Decided

## Context

T-021 requires three paid external design-partner engagements. The beta protocol and
evidence gate were merged in PR #9, but recruitment could not begin consistently until
the project owner approved a fee, currency, and service cap.

## Ruling

Each ChartworkAI concierge beta engagement costs **USD $300 plus applicable tax** and
is capped at **six total service hours per project**.

The existing standard engagement remains unchanged: preparation and suitability
screening, one guided installation and customization session of up to 90 minutes, a
14-day use period, and one 30-minute follow-up. Support and preparation count toward
the six-hour cap.

Payment method, payment deadline, cancellation or refund terms, tax treatment, and
any jurisdiction-specific contract language must be stated in the private written
proposal before each engagement. They are not inferred by this decision.

## Rationale

A fixed price and explicit service cap make the three engagements comparable, test
whether an external buyer will pay for guided governance onboarding, and bound the
delivery cost during the beta. Keeping unapproved legal and payment mechanics out of
the public framework avoids inventing commercial terms the owner did not authorize.

## Implementation notes

- Update the public recruitment template and beta protocol with the approved fee and
  cap.
- Keep invoices, payment records, customer identities, and signed terms outside Git.
- Record only the `payment_confirmed` attestation in public beta evidence.

## Consequences per agent

- **Orchestrator:** recruits against one consistent offer and does not schedule an
  installation before private terms and payment are confirmed.
- **Audit & Research Analyst:** compares demand and delivery effort against the same
  price and cap for all three partners.
- **Dogfood & Compliance QA:** requires `payment_confirmed: true` in every accepted
  evidence record without requesting financial details.

## Related

- T-021, DEC-004, PR #9.

