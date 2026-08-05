"""Result types for ChartworkAI checks.

These are the stable, machine-readable contract consumed by ``--json``, CI, and
AI assistants driving ChartworkAI through the CLI or an MCP server.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _package_version() -> str:
    """The installed distribution's version.

    Read at call time rather than import time so that ``pyproject.toml`` stays the
    single source of truth for the number consumers see in ``--json``.
    """
    try:
        from importlib.metadata import version

        return version("chartworkai")
    except Exception:  # pragma: no cover - source checkout without install metadata
        return "0.0.0.dev0"


class Status:
    """Finding statuses. ``FAIL`` is the only status that affects the exit code."""

    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


@dataclass
class Finding:
    """A single check result.

    Attributes:
        check: Stable machine-readable check id (e.g. ``"required_file"``).
            Safe to match on programmatically; the ``message`` is not.
        status: One of ``Status.PASS`` / ``Status.FAIL`` / ``Status.WARN``.
        message: One-line human-readable summary.
        path: Repo-relative path the finding concerns, when applicable.
        details: Supporting lines (offending matches, duplicated headings, ...).
    """

    check: str
    status: str
    message: str
    path: Optional[str] = None
    details: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check": self.check,
            "status": self.status,
            "message": self.message,
            "path": self.path,
            "details": list(self.details),
        }


@dataclass
class Report:
    """The full outcome of a compliance run."""

    project_root: str
    profile: Optional[str]
    is_data_profile: bool
    framework_repo: bool
    findings: List[Finding] = field(default_factory=list)
    tool: str = "chartworkai"
    #: Derived from the installed distribution — never hard-coded, so a release
    #: bump cannot leave the reported version stale in a consumer's JSON.
    version: str = field(default_factory=lambda: _package_version())

    def add(
        self,
        check: str,
        status: str,
        message: str,
        path: Optional[str] = None,
        details: Optional[List[str]] = None,
    ) -> Finding:
        finding = Finding(
            check=check,
            status=status,
            message=message,
            path=path,
            details=list(details or []),
        )
        self.findings.append(finding)
        return finding

    def of_status(self, status: str) -> List[Finding]:
        return [f for f in self.findings if f.status == status]

    @property
    def passed(self) -> int:
        return len(self.of_status(Status.PASS))

    @property
    def failed(self) -> int:
        return len(self.of_status(Status.FAIL))

    @property
    def warnings(self) -> int:
        return len(self.of_status(Status.WARN))

    def ok(self, strict: bool = False) -> bool:
        """True when the project passes. Under ``strict``, warnings also fail."""
        if self.failed:
            return False
        return not (strict and self.warnings)

    def exit_code(self, strict: bool = False) -> int:
        return 0 if self.ok(strict=strict) else 1

    def to_dict(self, strict: bool = False) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "version": self.version,
            "project_root": self.project_root,
            "profile": self.profile,
            "is_data_profile": self.is_data_profile,
            "framework_repo": self.framework_repo,
            "summary": {
                "passed": self.passed,
                "failed": self.failed,
                "warnings": self.warnings,
                "ok": self.ok(strict=strict),
            },
            "findings": [f.to_dict() for f in self.findings],
        }
