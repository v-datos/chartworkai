"""A Model Context Protocol server exposing ChartworkAI to any AI assistant.

This is what turns ChartworkAI from a linter you remember to run into governance an
assistant enforces natively: the assistant can check project health, read where the
project stands, and record decisions and handoffs — without a human relaying output.

MCP is JSON-RPC 2.0 over newline-delimited stdio, so this is implemented with the
standard library alone. ChartworkAI takes no runtime dependencies, and adding an SDK
purely to speak a documented wire protocol would break that promise.

Run it with ``chartworkai mcp``.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TextIO

from chartworkai import __version__
from chartworkai.checks import run_checks
from chartworkai.state import NAMESPACES, file_decision, file_handoff, read_state

#: Protocol revisions this server actually implements. The lifecycle spec requires
#: responding with a version we support — echoing back whatever the client asked
#: for would claim conformance to revisions we have never implemented.
#: A single JSON-RPC message larger than this is refused unread. The transport is
#: newline-delimited, so one oversized line would otherwise be buffered whole.
MAX_MESSAGE_BYTES = 1 << 20

SUPPORTED_PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
DEFAULT_PROTOCOL_VERSION = SUPPORTED_PROTOCOL_VERSIONS[0]

# JSON-RPC error codes (the subset this server can raise).
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

_PATH_PROPERTY = {
    "type": "string",
    "description": "Project root. Defaults to the server's working directory.",
}


def _tool_definitions() -> List[Dict[str, Any]]:
    return [
        {
            "name": "chartworkai_check",
            "description": (
                "Verify a project's governance layer is installed and healthy. Returns a "
                "structured report of every check with pass/fail/warn status. Use this "
                "before declaring any milestone done."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": _PATH_PROPERTY,
                    "strict": {
                        "type": "boolean",
                        "description": "Treat warnings as failures.",
                        "default": False,
                    },
                },
            },
        },
        {
            "name": "chartworkai_state",
            "description": (
                "Read where the project stands: profile, current phase, verify command, "
                "in-progress and queued tasks, blockers, and the most recent decisions and "
                "handoffs. Use this at the start of a session to decide the next dispatch."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {"path": _PATH_PROPERTY},
            },
        },
        {
            "name": "chartworkai_file_decision",
            "description": (
                "Record a decision as a dated, authority-stamped file. File one whenever a "
                "choice changes scope, a schema, a convention, or an interpretation — that "
                "is what makes the reasoning auditable months later. Returns the charter row "
                "you must then add to PROJECT_CHARTER.md."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Short imperative title."},
                    "authority": {
                        "type": "string",
                        "description": "Who decided, e.g. 'Orchestrator' or a named role.",
                    },
                    "context": {
                        "type": "string",
                        "description": "The situation and options considered.",
                    },
                    "ruling": {"type": "string", "description": "What was decided."},
                    "rationale": {"type": "string", "description": "Why. Optional but valued."},
                    "namespace": {
                        "type": "string",
                        "enum": list(NAMESPACES),
                        "description": (
                            "DEC = methodology/scope, DQ = data quality, "
                            "SC = software/config, MD = model design."
                        ),
                        "default": "DEC",
                    },
                    "path": _PATH_PROPERTY,
                },
                "required": ["title", "authority", "context", "ruling"],
            },
        },
        {
            "name": "chartworkai_file_handoff",
            "description": (
                "Write a dated handoff note — the currency passed between agents. Write one "
                "at a phase boundary or when ending a session, so the next agent can resume "
                "from files rather than chat history."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string", "description": "The role handing off."},
                    "produced": {"type": "string", "description": "What was produced."},
                    "location": {"type": "string", "description": "Where it lives (paths)."},
                    "limitations": {"type": "string", "description": "Known limitations."},
                    "verification": {"type": "string", "description": "How to verify it."},
                    "next_agent": {"type": "string", "description": "Next agent in the chain."},
                    "path": _PATH_PROPERTY,
                },
                "required": ["agent", "produced", "location"],
            },
        },
    ]


# --- Tool implementations ----------------------------------------------------


def _root(arguments: Dict[str, Any]) -> Path:
    """Resolve the requested project root, confined to the server's workspace.

    An MCP tool is driven by a model acting on text it did not author, so the path
    argument is attacker-influenced in the prompt-injection sense. Confining it to
    the directory the server was started in means the worst a poisoned instruction
    achieves is touching the workspace the operator already pointed us at.

    Set ``CHARTWORKAI_ALLOW_ANY_PATH=1`` to opt out when deliberately driving
    several repositories from one server.
    """
    workspace = Path.cwd().resolve()
    requested = Path(arguments.get("path") or ".").expanduser().resolve()

    if os.environ.get("CHARTWORKAI_ALLOW_ANY_PATH") == "1":
        return requested
    try:
        requested.relative_to(workspace)
    except ValueError:
        raise ValueError(
            f"path {requested} is outside this server's workspace ({workspace}). "
            "Start the server in that directory, or set CHARTWORKAI_ALLOW_ANY_PATH=1 "
            "to allow it deliberately."
        ) from None
    return requested


def _tool_check(arguments: Dict[str, Any]) -> Dict[str, Any]:
    strict = bool(arguments.get("strict", False))
    report = run_checks(_root(arguments))
    return report.to_dict(strict=strict)


def _tool_state(arguments: Dict[str, Any]) -> Dict[str, Any]:
    return read_state(_root(arguments))


def _tool_file_decision(arguments: Dict[str, Any]) -> Dict[str, Any]:
    return file_decision(
        _root(arguments),
        title=arguments["title"],
        authority=arguments["authority"],
        context=arguments["context"],
        ruling=arguments["ruling"],
        rationale=arguments.get("rationale", ""),
        namespace=arguments.get("namespace", "DEC"),
    )


def _tool_file_handoff(arguments: Dict[str, Any]) -> Dict[str, Any]:
    return file_handoff(
        _root(arguments),
        agent=arguments["agent"],
        produced=arguments["produced"],
        location=arguments["location"],
        limitations=arguments.get("limitations", ""),
        verification=arguments.get("verification", ""),
        next_agent=arguments.get("next_agent", ""),
    )


TOOLS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "chartworkai_check": _tool_check,
    "chartworkai_state": _tool_state,
    "chartworkai_file_decision": _tool_file_decision,
    "chartworkai_file_handoff": _tool_file_handoff,
}


# --- JSON-RPC plumbing -------------------------------------------------------


def _result(request_id: Any, result: Dict[str, Any]) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _tool_result(payload: Dict[str, Any], is_error: bool = False) -> Dict[str, Any]:
    """Wrap a payload as MCP tool content.

    The JSON is returned as text because that is what every MCP client can render
    and what a model can read directly.
    """
    return {
        "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
        "isError": is_error,
    }


def handle_message(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Handle one JSON-RPC message. Returns ``None`` for notifications.

    JSON-RPC 2.0 forbids replying to a notification (a message with no ``id``),
    whatever method it names, so the reply is suppressed here in one place rather
    than being remembered at every return.
    """
    response = _dispatch(message)
    return None if "id" not in message else response


def _dispatch(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}
    is_notification = "id" not in message

    if not isinstance(method, str):
        return None if is_notification else _error(request_id, INVALID_REQUEST, "missing method")

    if method == "initialize":
        requested = params.get("protocolVersion")
        negotiated = (
            requested
            if isinstance(requested, str) and requested in SUPPORTED_PROTOCOL_VERSIONS
            else DEFAULT_PROTOCOL_VERSION
        )
        return _result(
            request_id,
            {
                "protocolVersion": negotiated,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "chartworkai", "version": __version__},
                "instructions": (
                    "ChartworkAI governs long-running projects. Call chartworkai_state at the "
                    "start of a session to see where things stand, chartworkai_check before "
                    "declaring work done, and record every scope- or convention-changing "
                    "choice with chartworkai_file_decision."
                ),
            },
        )

    if method.startswith("notifications/"):
        return None

    if method == "ping":
        return None if is_notification else _result(request_id, {})

    if method == "tools/list":
        return _result(request_id, {"tools": _tool_definitions()})

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name not in TOOLS:
            return _error(request_id, INVALID_PARAMS, f"unknown tool: {name}")
        if not isinstance(arguments, dict):
            return _error(request_id, INVALID_PARAMS, "arguments must be an object")
        try:
            payload = TOOLS[name](arguments)
        except KeyError as exc:
            return _result(
                request_id, _tool_result({"error": f"missing argument: {exc.args[0]}"}, True)
            )
        except (ValueError, OSError) as exc:
            return _result(request_id, _tool_result({"error": str(exc)}, True))
        return _result(request_id, _tool_result(payload))

    if is_notification:
        return None
    return _error(request_id, METHOD_NOT_FOUND, f"unknown method: {method}")


def serve(stdin: Optional[TextIO] = None, stdout: Optional[TextIO] = None) -> int:
    """Serve MCP over newline-delimited JSON on stdio until stdin closes."""
    source = stdin if stdin is not None else sys.stdin
    sink = stdout if stdout is not None else sys.stdout

    for line in source:
        line = line.strip()
        if not line:
            continue
        if len(line) > MAX_MESSAGE_BYTES:
            # Refuse before parsing: the cost of the attack is in json.loads.
            response: Optional[Dict[str, Any]] = _error(
                None, INVALID_REQUEST, f"message exceeds {MAX_MESSAGE_BYTES} bytes"
            )
            sink.write(json.dumps(response) + "\n")
            sink.flush()
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            response = _error(None, PARSE_ERROR, "invalid JSON")
        except RecursionError:
            # CPython's JSON parser recurses per nesting level, so deeply nested input
            # raises rather than returning. Uncaught, one hostile message ended the
            # session for every later request — the arguments come from an assistant
            # acting on text it did not author, so this is reachable input.
            response = _error(None, INVALID_REQUEST, "message nesting is too deep")
        else:
            if isinstance(message, dict):
                try:
                    response = handle_message(message)
                except RecursionError:
                    response = _error(
                        message.get("id"), INVALID_REQUEST, "message nesting is too deep"
                    )
                except Exception as exc:  # never let one bad call kill the server
                    response = _error(message.get("id"), INTERNAL_ERROR, str(exc))
            else:
                response = _error(None, INVALID_REQUEST, "message must be an object")

        if response is not None:
            sink.write(json.dumps(response) + "\n")
            sink.flush()
    return 0
