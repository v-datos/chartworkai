import json
import subprocess
import sys
from pathlib import Path

from scripts.check_beta_evidence import PARTNER_IDS, check_directory, validate_record

ROOT = Path(__file__).resolve().parents[1]


def _record(partner_id: str, permission: str = "none") -> dict:
    record = {
        "schema_version": 1,
        "partner_id": partner_id,
        "external_partner": True,
        "payment_confirmed": True,
        "participant_operated": True,
        "install_source": "pypi",
        "project_profile": "generic",
        "workstream_count": 3,
        "os_family": "linux",
        "chartworkai_version": "0.2.0",
        "install_date": "2026-01-01",
        "setup_seconds": 2700,
        "setup_minutes": 45,
        "strict_compliance_passed": True,
        "first_governed_action": "task",
        "follow_up_date": "2026-01-15",
        "continued_use": True,
        "intervention_codes": ["DOC"],
        "case_study_permission": permission,
    }
    if permission != "none":
        record["case_study_approved_at"] = "2026-01-16"
        record["private_evidence_ref"] = f"CONSENT-{partner_id}-01"
    return record


def _write_records(directory: Path) -> None:
    directory.mkdir()
    for index, partner_id in enumerate(PARTNER_IDS):
        permission = "anonymized" if index == 0 else "none"
        (directory / f"{partner_id}.json").write_text(
            json.dumps(_record(partner_id, permission)), encoding="utf-8"
        )


def test_complete_three_partner_evidence_passes(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    _write_records(evidence)

    report = check_directory(evidence)

    assert report["ready"] is True
    assert report["records_found"] == 3
    assert report["publishable_case_studies"] == 1


def test_missing_partner_and_case_study_keep_task_open(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "P-001.json").write_text(json.dumps(_record("P-001")), encoding="utf-8")

    report = check_directory(evidence)

    assert report["ready"] is False
    assert report["records_found"] == 1
    errors = [error for finding in report["findings"] for error in finding["errors"]]
    assert errors.count("evidence record is missing") == 2
    assert "at least one partner must approve a final case study" in errors


def test_record_rejects_private_or_unstructured_fields() -> None:
    record = _record("P-001", "anonymized")
    record["partner_email"] = "person@example.test"
    record["notes"] = "free-form notes do not belong in public evidence"

    errors = validate_record(record, "P-001")

    assert any("privacy-sensitive keys" in error for error in errors)
    assert any("unknown keys" in error for error in errors)


def test_setup_minutes_must_match_timestamps() -> None:
    record = _record("P-001")
    record["setup_minutes"] = 44

    assert "setup_minutes must equal rounded-up setup seconds (45)" in validate_record(
        record, "P-001"
    )


def test_record_rejects_malformed_types_without_crashing() -> None:
    record = _record("P-001")
    record["schema_version"] = True
    record["workstream_count"] = True
    record["setup_seconds"] = True
    record["setup_minutes"] = True
    record["project_profile"] = []
    record["os_family"] = []
    record["first_governed_action"] = []
    record["intervention_codes"] = [{}]
    record["case_study_permission"] = []

    errors = validate_record(record, "P-001")

    assert len(errors) == 9


def test_cli_reports_not_ready_until_real_records_exist() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_beta_evidence.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    report = json.loads(result.stdout)
    assert result.returncode == 1
    assert report["ready"] is False
    assert report["records_found"] == 0
