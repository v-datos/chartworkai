"""ChartworkAI — the governance layer for agentic work.

Agent frameworks orchestrate. ChartworkAI governs: charter, decisions, handoffs,
and phase gates that survive across sessions, assistants, and months.
"""

from chartworkai.models import Finding, Report, Status, _package_version

#: Derived from the installed distribution so pyproject.toml is the only place a
#: release number is written.
__version__ = _package_version()

__all__ = ["Finding", "Report", "Status", "__version__"]
