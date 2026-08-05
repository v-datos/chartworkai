# Claims Gate & Evidence Ledger

This is the central staging ledger for claims, assertions, and findings. No claim may be referenced in published reports or findings documents unless it is **Promoted** (Tier 1 or Tier 2).

## Evidence Tiers

All assertions must be graded according to this scale:

| Tier | Definition | Examples |
|---|---|---|
| **Tier 1** | Direct, primary source evidence. Unaltered, verified raw source. | Official public registry documents, direct physical measurements/sensors, audio/video recordings. |
| **Tier 2** | Corroborated secondary source evidence. Verified by multiple independent sources. | Reports from reputable investigative organizations, peer-reviewed academic studies, multiple independent witnesses. |
| **Tier 3** | Uncorroborated assertion, single-source testimony, or rumor. | A single anonymous interview, social media posts, unverified claims. |

## Staging & Promotion Rules

1. **Staged:** All new assertions start as `Staged`. The team/assistant gathers evidence to verify the claim.
2. **Promoted:** A claim is promoted ONLY when it is graded **Tier 1** or **Tier 2**, and has a valid, verifiable source link. Only promoted claims may be cited in final deliverables.
3. **Demoted:** If an assertion is investigated and proven false or unverifiable, it is marked `Demoted` and retained in the ledger for transparency (prevents re-investigating the same rumor).

---

## Claims Ledger

<!--
  GUIDE: Fill this table. The verification script checks that:
  - Any claim with status 'Promoted' MUST be Tier 1 or Tier 2.
  - Any claim with status 'Promoted' MUST NOT have a placeholder or empty 'Source / Reference'.
-->

| ID | Claim | Source / Reference | Evidence Tier | Status | Date Updated |
|---|---|---|---|---|---|
| C-001 | {{Example: Company X received a sole-source contract}} | [{{Registry doc #123}}](file:///{{path/to/doc.pdf}}) | Tier 1 | Promoted | {{YYYY-MM-DD}} |
| C-002 | {{Example: Local river salinity exceeded standard thresholds}} | [{{Sensor Log v2}}](file:///{{data/sensor_log_v2.csv}}) | Tier 1 | Promoted | {{YYYY-MM-DD}} |
| C-003 | {{Example: Rumored land transfer to official's family}} | {{Investigation pending - single witness account}} | Tier 3 | Staged | {{YYYY-MM-DD}} |
| C-004 | {{Example: System crashed due to database pool exhaustion}} | [{{Syslog dump}}](file:///{{logs/syslog.txt}}) | Tier 1 | Promoted | {{YYYY-MM-DD}} |
| C-005 | {{Example: Alleged supply line diversion at location Y}} | {{Disproven: satellite photography confirms normal traffic}} | Tier 3 | Demoted | {{YYYY-MM-DD}} |

---

*Citations in report: Reference claims by their anchor ID, e.g., `According to the registry record [C-001](docs/investigation/claims_gate.md#C-001)...`*
