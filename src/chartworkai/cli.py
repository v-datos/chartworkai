"""ChartworkAI command-line interface.

    chartworkai init TARGET --name NAME [--slug SLUG] [--profile PROFILE | --profile-file FILE]
    chartworkai check [PATH] [--json] [--strict] [--quiet]
    chartworkai plan [PATH]
    chartworkai state [PATH]
    chartworkai mcp

Exit codes: ``0`` the project passes, ``1`` failures (or, under ``--strict``,
warnings), ``2`` usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from chartworkai import __version__
from chartworkai.checks import run_checks
from chartworkai.manifest import DEFAULT_PROFILE, KNOWN_PROFILES, LEGACY_PROFILE, PRESET_PROFILES
from chartworkai.models import Report, Status
from chartworkai.safety import UnsafePathError

_GLYPH = {Status.PASS: "PASS", Status.FAIL: "FAIL", Status.WARN: "WARN"}


def _render_text(report: Report, strict: bool, quiet: bool) -> str:
    lines: List[str] = []
    lines.append(f"ChartworkAI {__version__} — checking: {report.project_root}")
    profile = report.profile or f"{LEGACY_PROFILE} (legacy default)"
    scope = "framework repo" if report.framework_repo else "project"
    lines.append(f"Profile: {profile}  ({scope})")
    lines.append("")

    for finding in report.findings:
        if quiet and finding.status == Status.PASS:
            continue
        lines.append(f"{_GLYPH[finding.status]} {finding.message}")
        for detail in finding.details:
            lines.append(f"     {detail}")

    lines.append("")
    lines.append(f"{report.passed} passed, {report.failed} failed, {report.warnings} warning(s).")
    if report.ok(strict=strict):
        lines.append("ChartworkAI check passed.")
    elif report.failed:
        lines.append(f"ChartworkAI check failed with {report.failed} issue(s).")
    else:
        lines.append(f"ChartworkAI check failed: {report.warnings} warning(s) under --strict.")
    return "\n".join(lines)


def _cmd_check(args: argparse.Namespace) -> int:
    report = run_checks(args.path, self_audit=args.self_audit)
    if args.json:
        json.dump(report.to_dict(strict=args.strict), sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(_render_text(report, strict=args.strict, quiet=args.quiet))
    return report.exit_code(strict=args.strict)


def _cmd_init(args: argparse.Namespace) -> int:
    from chartworkai.scaffold import init_project

    try:
        summary = init_project(
            args.target,
            args.name,
            project_slug=args.slug,
            profile=args.profile or DEFAULT_PROFILE,
            profile_file=args.profile_file,
            force=args.force,
        )
    except (ValueError, NotADirectoryError, UnsafePathError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        json.dump(summary, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    print(f"\nInitialized {summary['project']} at {summary['project_root']}\n")
    print("Next steps:")
    print(
        "  1. Fill every {{...}} placeholder in AGENTS.md and the charter ## Stack "
        "block, then customize PROJECT_CHARTER.md."
    )
    print("  2. Explore optional extensions in ./_framework_extensions/.")
    print("  3. Re-run `chartworkai check .` until it passes.")
    print("  4. Delete the temporary ./_framework_* folders once customization is complete.\n")
    print("Compliance check now (unresolved {{...}} placeholders are EXPECTED):\n")

    report = run_checks(summary["project_root"])
    print(_render_text(report, strict=False, quiet=True))
    return 0


def _cmd_plan(args: argparse.Namespace) -> int:
    from chartworkai.plan import generate_phase_plan

    try:
        summary = generate_phase_plan(args.path)
    except (FileNotFoundError, UnsafePathError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        json.dump(summary, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(
            f"Regenerated {summary['file']} — Phase {summary['current_phase']} "
            f"({summary['phase_title']}), {summary['lines']} lines."
        )
    return 0


def _cmd_state(args: argparse.Namespace) -> int:
    from chartworkai.state import read_state

    root = Path(args.path)
    if not root.is_dir():
        print(f"error: not a directory: {args.path}", file=sys.stderr)
        return 1
    if not (root / "PROJECT_CHARTER.md").is_file():
        # Reporting state for a project that does not exist would mislead any agent
        # consuming this, which is worse than failing.
        print(
            f"error: no PROJECT_CHARTER.md in {args.path} — not a ChartworkAI project",
            file=sys.stderr,
        )
        return 1

    json.dump(read_state(args.path), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def _cmd_mcp(args: argparse.Namespace) -> int:
    from chartworkai.mcp_server import serve

    return serve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chartworkai",
        description=(
            "The governance layer for agentic work — charter, decisions, handoffs, "
            "and phase gates that survive across sessions, assistants, and months."
        ),
    )
    parser.add_argument("--version", action="version", version=f"chartworkai {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    init = subparsers.add_parser("init", help="Scaffold a new project's governance layer.")
    init.add_argument("target", help="Directory to create the project in.")
    init.add_argument("--name", required=True, help="Human-readable project name.")
    init.add_argument("--slug", default=None, help="Machine-friendly slug (derived if omitted).")
    profile_group = init.add_mutually_exclusive_group()
    profile_group.add_argument(
        "--profile",
        default=None,
        choices=list(KNOWN_PROFILES),
        metavar="PROFILE",
        help=(
            "Optional built-in preset: "
            + ", ".join(PRESET_PROFILES)
            + f". Omit for the project-agnostic {DEFAULT_PROFILE!r} core."
        ),
    )
    profile_group.add_argument(
        "--profile-file",
        default=None,
        metavar="FILE",
        help=(
            "JSON custom profile extending generic or a built-in preset. The validated "
            "contract is copied to chartworkai.profile.json in the project."
        ),
    )
    init.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing governance layer, discarding those documents.",
    )
    init.add_argument("--json", action="store_true", help="Emit a machine-readable summary.")
    init.set_defaults(func=_cmd_init)

    plan = subparsers.add_parser(
        "plan", help="Regenerate docs/phase_plan.md from the repository's current state."
    )
    plan.add_argument("path", nargs="?", default=".", help="Project root (default: cwd).")
    plan.add_argument("--json", action="store_true", help="Emit a machine-readable summary.")
    plan.set_defaults(func=_cmd_plan)

    check = subparsers.add_parser(
        "check", help="Verify a project's governance layer is installed and healthy."
    )
    check.add_argument(
        "path", nargs="?", default=".", help="Project root to check (default: current directory)."
    )
    check.add_argument(
        "--json", action="store_true", help="Emit machine-readable JSON (for CI and AI agents)."
    )
    check.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    check.add_argument("--quiet", action="store_true", help="Only show failures and warnings.")
    check.add_argument(
        "--self-audit",
        action="store_true",
        help=(
            "Audit ChartworkAI's own repository. Relaxes the placeholder, scaffold and "
            "assistant-name checks, whose targets are this product's content. Do not "
            "use it on a project built with ChartworkAI."
        ),
    )
    check.set_defaults(func=_cmd_check)

    state = subparsers.add_parser(
        "state",
        help="Print where the project stands as JSON (phase, tasks, recent decisions).",
    )
    state.add_argument("path", nargs="?", default=".", help="Project root (default: cwd).")
    state.set_defaults(func=_cmd_state)

    mcp = subparsers.add_parser(
        "mcp",
        help="Run as an MCP server over stdio so any AI assistant can drive ChartworkAI.",
    )
    mcp.set_defaults(func=_cmd_mcp)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
