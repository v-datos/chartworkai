# Concierge Beta Evidence

This directory contains only de-identified, publication-safe evidence for T-021.
Use `record.example.json` as the schema example and create exactly three completed
records named `P-001.json`, `P-002.json`, and `P-003.json`.

Do not commit names, organization names, email addresses, repository URLs or paths,
source code, credentials, payment details, signatures, meeting links, recordings,
screenshots, raw notes, or confidential project descriptions.

Each Boolean and timestamp is an operator attestation backed by a private source
record. `private_evidence_ref` values must be non-identifying lookup codes. They let
the owner audit the claim without publishing the underlying private material.

Run:

```bash
python scripts/check_beta_evidence.py
```

The command fails until exactly three complete partner records exist and at least
one has final case-study publication approval.

