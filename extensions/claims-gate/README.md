# Extension: claims gate (investigation profile)

Establish a staging table and evidence-tier promotion system for investigative or knowledge-base projects. This prevents unverified assertions or rumors from contaminating published findings or reports. This extension packages the standout verification pattern from a Spanish-language corruption investigation, and the claim-demotion authority from a marine-ecology research project.

## Principles

- **Repo-native staging ledger.** All findings and the claims backing them are logged in a single repo-native markdown table. Nothing is cited in final reports unless it has graduated this gate.
- **Evidence tiers.** Every claim is rated on a strict, documented scale:
  - **Tier 1:** Direct, primary source evidence (e.g., official records, direct sensor data, original documents).
  - **Tier 2:** Corroborated secondary source evidence (e.g., independent news outlets, peer-reviewed citations, multiple independent testimonies).
  - **Tier 3:** Uncorroborated assertion, single-source testimony, or rumor.
- **Strict promotion rules.** Only Tier 1 and Tier 2 claims can have the status `Promoted` and be used in published findings. Tier 3 claims remain `Staged` (requiring further investigation) or are `Demoted`.
- **Automated compliance.** A validation script runs at build/commit time to fail the check if any `Promoted` claim is still marked `Tier 3` or is missing a source link.

## Adopt it

1. Copy `claims_gate.template.md` → `docs/investigation/claims_gate.md` (create the directory if needed).
2. Copy `check_claims.sh` → your project's `scripts/` directory.
3. In your `PROJECT_CHARTER.md`'s `## Stack` block, append `scripts/check_claims.sh docs/investigation/claims_gate.md` to your **Verify command**.
4. Log all claims in the ledger. Before you mention a claim in your findings:
   - Verify it is graded Tier 1 or Tier 2.
   - Set its status to `Promoted`.
   - Cite its ID (e.g., `[C-001](docs/investigation/claims_gate.md#C-001)`) in the findings text.

## Files

- `claims_gate.template.md` — the staging ledger and evidence tier definition template.
- `check_claims.sh` — the validation script to automate compliance checks.
