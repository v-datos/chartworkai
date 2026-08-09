#!/usr/bin/env python3
"""Validate the de-identified evidence required to close T-021."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

SCHEMA_VERSION = 1
PARTNER_IDS = ("P-001", "P-002", "P-003")
ALLOWED_KEYS = frozenset(
    {
        "schema_version",
        "partner_id",
        "external_partner",
        "payment_confirmed",
        "participant_operated",
        "install_source",
        "project_profile",
        "workstream_count",
        "os_family",
        "chartworkai_version",
        "install_date",
        "setup_seconds",
        "setup_minutes",
        "strict_compliance_passed",
        "first_governed_action",
        "follow_up_date",
        "continued_use",
        "intervention_codes",
        "case_study_permission",
        "case_study_approved_at",
        "private_evidence_ref",
    }
)
REQUIRED_KEYS = ALLOWED_KEYS - {"case_study_approved_at", "private_evidence_ref"}
OS_FAMILIES = frozenset({"linux", "macos", "windows"})
PROJECT_PROFILES = frozenset(
    {
        "generic",
        "software-app",
        "data-science",
        "database",
        "competition-ml",
        "investigation",
        "deployed-service",
        "custom",
    }
)
ACTIONS = frozenset({"task", "decision", "handoff", "state_review"})
INTERVENTIONS = frozenset({"ENV", "FIT", "DOC", "CHK", "GIT", "SEC", "INT", "OTHER"})
PERMISSIONS = frozenset({"named", "anonymized", "none"})
PRIVATE_KEY_RE = re.compile(
    r"(?:name|email|phone|address|organization|company|repo(?:sitory)?(?:_url|_path)?|"
    r"secret|token|password|credential|invoice|payment_detail|signature|recording)",
    re.IGNORECASE,
)
EVIDENCE_REF_RE = re.compile(r"^[A-Z][A-Z0-9-]{5,63}$")


def _date(value: Any, field: str, errors: List[str]) -> Optional[dt.date]:
    if not isinstance(value, str):
        errors.append(f"{field} must be an ISO date")
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        errors.append(f"{field} must be an ISO date")
        return None


def validate_record(data: Any, expected_id: str) -> List[str]:
    """Return validation errors for one public beta evidence record."""
    errors: List[str] = []
    if not isinstance(data, dict):
        return ["record must be a JSON object"]

    keys = set(data)
    private_keys = sorted(key for key in keys if PRIVATE_KEY_RE.search(key))
    if private_keys:
        errors.append("privacy-sensitive keys are forbidden: " + ", ".join(private_keys))
    unknown = sorted(keys - ALLOWED_KEYS)
    if unknown:
        errors.append("unknown keys are forbidden: " + ", ".join(unknown))
    missing = sorted(REQUIRED_KEYS - keys)
    if missing:
        errors.append("missing required keys: " + ", ".join(missing))
        return errors

    if type(data["schema_version"]) is not int or data["schema_version"] != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if data["partner_id"] != expected_id:
        errors.append(f"partner_id must match filename ({expected_id})")
    if data["external_partner"] is not True:
        errors.append("external_partner must be true")
    if data["payment_confirmed"] is not True:
        errors.append("payment_confirmed must be true")
    if data["participant_operated"] is not True:
        errors.append("participant_operated must be true")
    if data["install_source"] != "pypi":
        errors.append("install_source must be pypi")
    if (
        not isinstance(data["project_profile"], str)
        or data["project_profile"] not in PROJECT_PROFILES
    ):
        errors.append("project_profile must be a built-in profile or custom")
    if type(data["workstream_count"]) is not int or data["workstream_count"] < 3:
        errors.append("workstream_count must be an integer of at least 3")
    if not isinstance(data["os_family"], str) or data["os_family"] not in OS_FAMILIES:
        errors.append("os_family must be linux, macos, or windows")
    if not isinstance(data["chartworkai_version"], str) or not re.fullmatch(
        r"\d+\.\d+\.\d+(?:[a-zA-Z0-9.-]+)?", data["chartworkai_version"]
    ):
        errors.append("chartworkai_version must be a semantic version")

    install_date = _date(data["install_date"], "install_date", errors)
    follow_up_date = _date(data["follow_up_date"], "follow_up_date", errors)
    if follow_up_date and install_date and follow_up_date <= install_date:
        errors.append("follow_up_date must be after install_date")
    if type(data["setup_seconds"]) is not int or data["setup_seconds"] <= 0:
        errors.append("setup_seconds must be a positive integer")
    else:
        expected_minutes = math.ceil(data["setup_seconds"] / 60)
        if data["setup_minutes"] != expected_minutes:
            errors.append(f"setup_minutes must equal rounded-up setup seconds ({expected_minutes})")
    if type(data["setup_minutes"]) is not int or data["setup_minutes"] <= 0:
        errors.append("setup_minutes must be a positive integer")
    if data["strict_compliance_passed"] is not True:
        errors.append("strict_compliance_passed must be true")
    if (
        not isinstance(data["first_governed_action"], str)
        or data["first_governed_action"] not in ACTIONS
    ):
        errors.append("first_governed_action has an unsupported value")
    if not isinstance(data["continued_use"], bool):
        errors.append("continued_use must be a Boolean")

    codes = data["intervention_codes"]
    if not isinstance(codes, list) or any(
        not isinstance(code, str) or code not in INTERVENTIONS for code in codes
    ):
        errors.append("intervention_codes must be a list of documented codes")
    elif len(codes) != len(set(codes)):
        errors.append("intervention_codes must not contain duplicates")

    permission = data["case_study_permission"]
    if not isinstance(permission, str) or permission not in PERMISSIONS:
        errors.append("case_study_permission must be named, anonymized, or none")
    elif permission in {"named", "anonymized"}:
        if not data.get("case_study_approved_at"):
            errors.append("publishable case-study permission needs case_study_approved_at")
        else:
            approval_date = _date(data["case_study_approved_at"], "case_study_approved_at", errors)
            if approval_date and follow_up_date and approval_date < follow_up_date:
                errors.append("case_study_approved_at must not predate follow_up_date")
        ref = data.get("private_evidence_ref")
        if not isinstance(ref, str) or not EVIDENCE_REF_RE.fullmatch(ref):
            errors.append("publishable case-study permission needs a non-identifying evidence ref")
    elif "case_study_approved_at" in data or "private_evidence_ref" in data:
        errors.append("permission evidence must be absent when case_study_permission is none")

    return errors


def check_directory(directory: Path) -> Dict[str, Any]:
    """Validate the fixed three-partner evidence set."""
    findings: List[Dict[str, Any]] = []
    found_ids: List[str] = []

    unexpected = sorted(
        path.name
        for path in directory.glob("*.json")
        if path.name != "record.example.json" and path.stem not in PARTNER_IDS
    )
    if unexpected:
        findings.append(
            {"record": None, "errors": ["unexpected records: " + ", ".join(unexpected)]}
        )

    permissions = 0
    for partner_id in PARTNER_IDS:
        path = directory / f"{partner_id}.json"
        if not path.is_file():
            findings.append({"record": partner_id, "errors": ["evidence record is missing"]})
            continue
        found_ids.append(partner_id)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append({"record": partner_id, "errors": [f"cannot read valid JSON: {exc}"]})
            continue
        errors = validate_record(data, partner_id)
        if not errors and data["case_study_permission"] in {"named", "anonymized"}:
            permissions += 1
        findings.append({"record": partner_id, "errors": errors})

    if permissions < 1:
        findings.append(
            {"record": None, "errors": ["at least one partner must approve a final case study"]}
        )

    errors = sum(len(item["errors"]) for item in findings)
    return {
        "schema_version": SCHEMA_VERSION,
        "directory": str(directory),
        "expected_partners": len(PARTNER_IDS),
        "records_found": len(found_ids),
        "publishable_case_studies": permissions,
        "findings": findings,
        "ready": errors == 0,
    }


def _render_text(report: Dict[str, Any]) -> str:
    lines = ["ChartworkAI T-021 beta evidence", f"Directory: {report['directory']}", ""]
    for finding in report["findings"]:
        label = finding["record"] or "program"
        if finding["errors"]:
            lines.extend(f"FAIL {label}: {error}" for error in finding["errors"])
        else:
            lines.append(f"PASS {label}: evidence record is complete")
    lines.extend(
        [
            "",
            f"Records: {report['records_found']}/{report['expected_partners']}",
            f"Publishable case studies: {report['publishable_case_studies']}",
            "T-021 completion gate passed." if report["ready"] else "T-021 remains open.",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=Path("docs/beta/results"),
        help="Evidence directory (default: docs/beta/results).",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    report = check_directory(args.directory)
    if args.json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(_render_text(report))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
