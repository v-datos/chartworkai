"""Wire-protocol tests for :mod:`chartworkai.mcp_server`.

Two levels, both cheap and hermetic:

* :func:`handle_message` — one dict in, one dict (or ``None``) out. Every method,
  every error code, every tool.
* :func:`serve` — driven with ``io.StringIO`` rather than a real process, so the
  framing rules (one JSON object per line, notifications emit nothing, a bad line
  never kills the loop) are asserted directly.

One end-to-end subprocess test pipes a real handshake through the installed CLI to
prove the ``chartworkai mcp`` wiring holds outside the test process.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest
from conftest import age, write

from chartworkai import __version__
from chartworkai import mcp_server as server_module
from chartworkai.checks import run_checks
from chartworkai.mcp_server import TOOLS, handle_message, serve
from chartworkai.state import NAMESPACES, read_state


@pytest.fixture(autouse=True)
def _allow_tmp_paths(monkeypatch):
    """Let these tests address projects under ``tmp_path``.

    The server confines tool paths to its working directory, which is a real
    protection (an MCP tool argument is prompt-influenced). These tests exercise
    tool *behaviour*, not confinement, and their fixtures live outside the cwd — so
    they take the documented escape hatch. ``TestWorkspaceConfinement`` below turns
    it off and asserts the guard itself.
    """
    monkeypatch.setenv("CHARTWORKAI_ALLOW_ANY_PATH", "1")


# The wire values, written out rather than imported: these are the protocol, not
# an implementation detail, so a test must fail if the module ever redefines them.
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
DEFAULT_PROTOCOL_VERSION = "2025-06-18"

TOOL_NAMES = [
    "chartworkai_check",
    "chartworkai_state",
    "chartworkai_file_decision",
    "chartworkai_file_handoff",
]
WRITER_TOOLS = ["chartworkai_file_decision", "chartworkai_file_handoff"]
REQUIRED_ARGUMENTS = {
    "chartworkai_check": [],
    "chartworkai_state": [],
    "chartworkai_file_decision": ["title", "authority", "context", "ruling"],
    "chartworkai_file_handoff": ["agent", "produced", "location"],
}


# --- Message helpers ----------------------------------------------------------


def message(method: str, request_id: Any = 1, **params: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}


def notification(method: str, **params: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "method": method, "params": params}


def arguments_for(name: str, project: Path, **overrides: Any) -> Dict[str, Any]:
    """The minimal valid argument set for *name*."""
    base: Dict[str, Any] = {"path": str(project)}
    if name == "chartworkai_file_decision":
        base.update(title="Adopt Postgres", authority="Orchestrator", context="c", ruling="r")
    elif name == "chartworkai_file_handoff":
        base.update(agent="Data Engineer", produced="a loader", location="src/etl")
    base.update(overrides)
    return base


def call(name: str, arguments: Dict[str, Any], request_id: Any = 1) -> Dict[str, Any]:
    return handle_message(message("tools/call", request_id, name=name, arguments=arguments))


def payload(response: Dict[str, Any]) -> Any:
    """The tool's JSON payload, decoded from its text content block."""
    return json.loads(response["result"]["content"][0]["text"])


def tool_definitions() -> List[Dict[str, Any]]:
    return handle_message(message("tools/list"))["result"]["tools"]


def definition(name: str) -> Dict[str, Any]:
    return next(t for t in tool_definitions() if t["name"] == name)


def run_serve(*lines: str) -> List[str]:
    """Feed *lines* through ``serve`` and return the raw output lines."""
    sink = io.StringIO()
    assert serve(io.StringIO("".join(f"{line}\n" for line in lines)), sink) == 0
    text = sink.getvalue()
    assert text == "" or text.endswith("\n"), "every response must be newline-terminated"
    return text.splitlines()


def served(*lines: str) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in run_serve(*lines)]


def encoded(*messages: Dict[str, Any]) -> List[str]:
    return [json.dumps(m) for m in messages]


# --- Protocol constants -------------------------------------------------------


class TestProtocolConstants:
    @pytest.mark.parametrize(
        "name, value",
        [
            ("PARSE_ERROR", PARSE_ERROR),
            ("INVALID_REQUEST", INVALID_REQUEST),
            ("METHOD_NOT_FOUND", METHOD_NOT_FOUND),
            ("INVALID_PARAMS", INVALID_PARAMS),
            ("INTERNAL_ERROR", INTERNAL_ERROR),
            ("DEFAULT_PROTOCOL_VERSION", DEFAULT_PROTOCOL_VERSION),
        ],
    )
    def test_the_module_uses_the_documented_wire_values(self, name, value):
        assert getattr(server_module, name) == value


# --- initialize ---------------------------------------------------------------


class TestInitialize:
    def test_result_shape(self):
        result = handle_message(message("initialize"))["result"]
        assert result["capabilities"]["tools"] == {"listChanged": False}
        assert result["serverInfo"] == {"name": "chartworkai", "version": __version__}
        assert isinstance(result["instructions"], str) and result["instructions"]

    @pytest.mark.parametrize("requested", ["2024-11-05", "2025-06-18", "2025-03-26"])
    def test_a_string_protocol_version_is_echoed(self, requested):
        response = handle_message(message("initialize", protocolVersion=requested))
        assert response["result"]["protocolVersion"] == requested

    @pytest.mark.parametrize("requested", [None, 7, 2025.06, ["2025-06-18"], {"v": 1}, True])
    def test_a_non_string_protocol_version_falls_back_to_the_default(self, requested):
        response = handle_message(message("initialize", protocolVersion=requested))
        assert response["result"]["protocolVersion"] == DEFAULT_PROTOCOL_VERSION

    def test_missing_params_falls_back_to_the_default(self):
        response = handle_message({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        assert response["result"]["protocolVersion"] == DEFAULT_PROTOCOL_VERSION

    def test_the_envelope_is_json_rpc_2(self):
        response = handle_message(message("initialize", "abc"))
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == "abc"
        assert "error" not in response


# --- tools/list ---------------------------------------------------------------


class TestToolsList:
    def test_exactly_the_four_tools_in_order(self):
        assert [t["name"] for t in tool_definitions()] == TOOL_NAMES

    def test_the_advertised_list_matches_the_dispatch_table(self):
        assert sorted(TOOLS) == sorted(TOOL_NAMES)

    @pytest.mark.parametrize("name", TOOL_NAMES)
    def test_every_tool_documents_itself(self, name):
        tool = definition(name)
        assert set(tool) == {"name", "description", "inputSchema"}
        assert isinstance(tool["description"], str)
        assert len(tool["description"]) > 40

    @pytest.mark.parametrize("name", TOOL_NAMES)
    def test_input_schema_is_a_well_formed_object_schema(self, name):
        schema = definition(name)["inputSchema"]
        assert schema["type"] == "object"
        assert isinstance(schema["properties"], dict) and schema["properties"]
        for prop in schema["properties"].values():
            assert prop["type"] in {"string", "boolean", "number", "integer"}
            assert isinstance(prop["description"], str) and prop["description"]

    @pytest.mark.parametrize("name", TOOL_NAMES)
    def test_required_lists_only_declared_properties(self, name):
        schema = definition(name)["inputSchema"]
        required = schema.get("required", [])
        assert required == REQUIRED_ARGUMENTS[name]
        assert set(required) <= set(schema["properties"])

    @pytest.mark.parametrize("name", TOOL_NAMES)
    def test_every_tool_accepts_a_project_path(self, name):
        assert definition(name)["inputSchema"]["properties"]["path"]["type"] == "string"

    def test_the_namespace_enum_tracks_the_state_module(self):
        schema = definition("chartworkai_file_decision")["inputSchema"]
        namespace = schema["properties"]["namespace"]
        assert namespace["enum"] == list(NAMESPACES)
        assert namespace["default"] == "DEC"

    def test_strict_defaults_to_false(self):
        strict = definition("chartworkai_check")["inputSchema"]["properties"]["strict"]
        assert strict["type"] == "boolean"
        assert strict["default"] is False

    def test_the_schema_is_json_serialisable(self):
        assert json.loads(json.dumps(tool_definitions())) == tool_definitions()


# --- tools/call: the common envelope ------------------------------------------


class TestToolCallEnvelope:
    @pytest.mark.parametrize("name", TOOL_NAMES)
    def test_content_is_one_json_text_block(self, project, name):
        response = call(name, arguments_for(name, project))
        result = response["result"]
        assert set(result) == {"content", "isError"}
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert isinstance(payload(response), dict)

    @pytest.mark.parametrize("name", TOOL_NAMES)
    def test_is_error_is_false_on_success(self, project, name):
        assert call(name, arguments_for(name, project))["result"]["isError"] is False

    @pytest.mark.parametrize("name", TOOL_NAMES)
    def test_the_request_id_is_echoed(self, project, name):
        response = call(name, arguments_for(name, project), request_id="req-9")
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == "req-9"

    @pytest.mark.parametrize("name", ["chartworkai_check", "chartworkai_state"])
    def test_an_omitted_path_defaults_to_the_working_directory(self, project, monkeypatch, name):
        monkeypatch.chdir(project)
        assert payload(call(name, {}))["project_root"] == str(project.resolve())


# --- tools/call: chartworkai_check ----------------------------------------------


class TestCheckTool:
    def test_payload_matches_the_json_report_contract(self, project):
        assert payload(call("chartworkai_check", {"path": str(project)})) == run_checks(
            project
        ).to_dict(strict=False)

    def test_it_reports_failures_without_flagging_a_protocol_error(self, project):
        (project / "TASKS.md").unlink()
        response = call("chartworkai_check", {"path": str(project)})
        report = payload(response)
        assert response["result"]["isError"] is False  # the call worked; the project did not
        assert report["summary"]["ok"] is False
        assert report["summary"]["failed"] >= 1

    def test_strict_turns_warnings_into_a_failed_summary(self, project):
        age(project / "STATUS.md", days=20)
        lenient = payload(call("chartworkai_check", {"path": str(project)}))
        strict = payload(call("chartworkai_check", {"path": str(project), "strict": True}))
        assert lenient["summary"]["warnings"] == 1
        assert lenient["summary"]["ok"] is True
        assert strict["summary"]["ok"] is False
        assert strict == run_checks(project).to_dict(strict=True)

    @pytest.mark.parametrize("strict", [True, "yes", 1])
    def test_truthy_strict_values_are_honoured(self, project, strict):
        age(project / "STATUS.md", days=20)
        arguments = {"path": str(project), "strict": strict}
        assert payload(call("chartworkai_check", arguments))["summary"]["ok"] is False

    @pytest.mark.parametrize("strict", [False, 0, "", None])
    def test_falsy_strict_values_stay_lenient(self, project, strict):
        age(project / "STATUS.md", days=20)
        arguments = {"path": str(project), "strict": strict}
        assert payload(call("chartworkai_check", arguments))["summary"]["ok"] is True


# --- tools/call: chartworkai_state ----------------------------------------------


class TestStateTool:
    def test_payload_matches_read_state(self, project):
        assert payload(call("chartworkai_state", {"path": str(project)})) == read_state(project)

    def test_it_answers_for_a_directory_with_no_governance_layer(self, tmp_path):
        bare = tmp_path / "bare"
        bare.mkdir()
        assert payload(call("chartworkai_state", {"path": str(bare)}))["project"] == "bare"


# --- tools/call: the writers --------------------------------------------------


class TestWriterTools:
    def test_a_decision_is_written_under_the_given_path(self, project):
        name = "chartworkai_file_decision"
        result = payload(call(name, arguments_for(name, project)))
        assert (project / result["file"]).is_file()
        assert result["file"].startswith("docs/decisions/")
        assert set(result) == {"id", "file", "charter_row", "next_step"}

    def test_a_handoff_is_written_under_the_given_path(self, project):
        name = "chartworkai_file_handoff"
        result = payload(call(name, arguments_for(name, project)))
        assert (project / result["file"]).is_file()
        assert result["file"].startswith("docs/handoffs/")
        assert result["agent"] == "Data Engineer"

    def test_the_writers_create_the_directories_they_need(self, tmp_path):
        bare = tmp_path / "bare"
        bare.mkdir()
        for name in WRITER_TOOLS:
            assert (bare / payload(call(name, arguments_for(name, bare)))["file"]).is_file()

    @pytest.mark.parametrize("namespace", NAMESPACES)
    def test_the_namespace_argument_is_passed_through(self, project, namespace):
        arguments = arguments_for("chartworkai_file_decision", project, namespace=namespace)
        assert payload(call("chartworkai_file_decision", arguments))["id"].startswith(namespace)

    def test_optional_decision_fields_are_passed_through(self, project):
        arguments = arguments_for("chartworkai_file_decision", project, rationale="because")
        result = payload(call("chartworkai_file_decision", arguments))
        assert "## Rationale\n\nbecause" in (project / result["file"]).read_text(encoding="utf-8")

    def test_optional_handoff_fields_are_passed_through(self, project):
        arguments = arguments_for(
            "chartworkai_file_handoff",
            project,
            limitations="no backfill",
            verification="pytest -q",
            next_agent="Analyst",
        )
        result = payload(call("chartworkai_file_handoff", arguments))
        body = (project / result["file"]).read_text(encoding="utf-8")
        assert "no backfill" in body
        assert "pytest -q" in body
        assert "Analyst" in body


class TestToolErrorsAreReportedNotRaised:
    @pytest.mark.parametrize(
        "name, dropped",
        [(name, arg) for name in WRITER_TOOLS for arg in REQUIRED_ARGUMENTS[name]],
    )
    def test_a_missing_required_argument_returns_is_error(self, project, name, dropped):
        arguments = arguments_for(name, project)
        arguments.pop(dropped)
        response = call(name, arguments)
        assert response["result"]["isError"] is True
        assert payload(response)["error"] == f"missing argument: {dropped}"
        assert "error" not in response  # a tool failure is a result, not a protocol error

    def test_no_file_is_written_when_an_argument_is_missing(self, project):
        arguments = arguments_for("chartworkai_file_decision", project)
        arguments.pop("ruling")
        call("chartworkai_file_decision", arguments)
        assert not list((project / "docs" / "decisions").glob("*DEC002*"))

    @pytest.mark.parametrize("namespace", ["XX", "", "DECISION", "0"])
    def test_an_invalid_namespace_returns_a_readable_is_error(self, project, namespace):
        arguments = arguments_for("chartworkai_file_decision", project, namespace=namespace)
        response = call("chartworkai_file_decision", arguments)
        assert response["result"]["isError"] is True
        assert "DEC, DQ, SC, MD" in payload(response)["error"]
        assert repr(namespace) in payload(response)["error"]

    def test_an_unwritable_path_returns_is_error(self, tmp_path):
        blocker = tmp_path / "not-a-directory.md"
        blocker.write_text("# nope\n", encoding="utf-8")
        name = "chartworkai_file_decision"
        response = call(name, arguments_for(name, blocker))
        assert response["result"]["isError"] is True
        assert isinstance(payload(response)["error"], str)


# --- JSON-RPC error handling --------------------------------------------------


class TestProtocolErrors:
    def test_unknown_method(self):
        response = handle_message(message("wat/no"))
        assert response["error"]["code"] == METHOD_NOT_FOUND
        assert "wat/no" in response["error"]["message"]
        assert "result" not in response

    @pytest.mark.parametrize("method", ["tools/nope", "resources/list", "prompts/list", ""])
    def test_methods_this_server_does_not_implement(self, method):
        assert handle_message(message(method))["error"]["code"] == METHOD_NOT_FOUND

    def test_unknown_tool(self):
        response = handle_message(message("tools/call", name="chartworkai_nope"))
        assert response["error"]["code"] == INVALID_PARAMS
        assert "chartworkai_nope" in response["error"]["message"]

    def test_tools_call_without_a_name(self):
        assert handle_message(message("tools/call"))["error"]["code"] == INVALID_PARAMS

    @pytest.mark.parametrize("method", [None, 7, ["initialize"], {"m": 1}])
    def test_a_non_string_method_is_an_invalid_request(self, method):
        response = handle_message({"jsonrpc": "2.0", "id": 1, "method": method})
        assert response["error"]["code"] == INVALID_REQUEST
        assert response["error"]["message"] == "missing method"

    def test_a_message_with_no_method_at_all(self):
        assert handle_message({"jsonrpc": "2.0", "id": 1})["error"]["code"] == INVALID_REQUEST

    @pytest.mark.parametrize("request_id", [1, 0, -1, "abc", "", None])
    def test_the_id_is_echoed_verbatim_on_errors(self, request_id):
        response = handle_message({"jsonrpc": "2.0", "id": request_id, "method": "nope"})
        assert response["id"] == request_id
        assert response["jsonrpc"] == "2.0"

    def test_ping_with_an_id_returns_an_empty_result(self):
        assert handle_message(message("ping")) == {"jsonrpc": "2.0", "id": 1, "result": {}}


class TestNotifications:
    @pytest.mark.parametrize(
        "method",
        [
            "notifications/initialized",
            "notifications/cancelled",
            "notifications/progress",
            "ping",
            "unknown/method",
        ],
    )
    def test_a_notification_gets_no_response(self, method):
        assert handle_message(notification(method)) is None

    def test_a_message_without_method_or_id_gets_no_response(self):
        assert handle_message({"jsonrpc": "2.0"}) is None

    def test_a_notifications_method_is_silent_even_with_an_id(self):
        assert handle_message(message("notifications/initialized")) is None

    def test_an_explicit_null_id_is_still_a_request(self):
        # ``"id": null`` is present, so this is a (malformed) request, not a
        # notification: the server must answer rather than stay silent.
        response = handle_message({"jsonrpc": "2.0", "id": None, "method": "ping"})
        assert response == {"jsonrpc": "2.0", "id": None, "result": {}}


# --- serve(): framing ---------------------------------------------------------


class TestServeFraming:
    def test_no_input_produces_no_output(self):
        assert run_serve() == []

    @pytest.mark.parametrize("blank", ["", "   ", "\t"])
    def test_blank_lines_are_skipped(self, blank):
        assert run_serve(blank, blank) == []

    def test_one_response_per_request_line(self):
        lines = encoded(message("ping", 1), message("ping", 2), message("ping", 3))
        assert [r["id"] for r in served(*lines)] == [1, 2, 3]

    def test_notifications_emit_nothing(self):
        lines = encoded(
            notification("notifications/initialized"),
            notification("notifications/cancelled"),
            message("ping", 1),
        )
        assert [r["id"] for r in served(*lines)] == [1]

    def test_every_emitted_line_is_standalone_json(self, project):
        lines = encoded(
            message("initialize", 1),
            message("tools/list", 2),
            message("tools/call", 3, name="chartworkai_state", arguments={"path": str(project)}),
        )
        for raw in run_serve(*lines):
            assert json.loads(raw)["jsonrpc"] == "2.0"

    def test_a_pretty_printed_payload_still_occupies_one_line(self, project):
        line = json.dumps(
            message("tools/call", 1, name="chartworkai_state", arguments={"path": str(project)})
        )
        raw = run_serve(line)
        assert len(raw) == 1
        assert "\n" not in raw[0]
        assert "\n" in json.loads(raw[0])["result"]["content"][0]["text"]  # indent=2 inside

    def test_carriage_returns_are_tolerated(self):
        sink = io.StringIO()
        serve(io.StringIO(json.dumps(message("ping", 1)) + "\r\n"), sink)
        assert json.loads(sink.getvalue())["id"] == 1


class TestServeErrorRecovery:
    @pytest.mark.parametrize("bad", ["not json", "{", '{"jsonrpc": ', "}{", "nul"])
    def test_a_malformed_line_is_a_parse_error(self, bad):
        (response,) = served(bad)
        assert response == {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": PARSE_ERROR, "message": "invalid JSON"},
        }

    def test_the_loop_survives_a_malformed_line(self):
        responses = served("not json", json.dumps(message("ping", 2)), "also not json")
        assert [r["id"] for r in responses] == [None, 2, None]
        assert responses[0]["error"]["code"] == PARSE_ERROR
        assert responses[1]["result"] == {}
        assert responses[2]["error"]["code"] == PARSE_ERROR

    @pytest.mark.parametrize("raw", ["[]", "3", '"a string"', "null", "true", '[{"id": 1}]'])
    def test_a_non_object_message_is_an_invalid_request(self, raw):
        (response,) = served(raw)
        assert response["error"]["code"] == INVALID_REQUEST
        assert response["error"]["message"] == "message must be an object"
        assert response["id"] is None

    def test_a_non_object_arguments_value_is_rejected_and_the_loop_survives(self):
        # A non-dict "arguments" is rejected up front as invalid params rather than
        # being allowed to become an internal error deeper in the call.
        broken = json.dumps(message("tools/call", 1, name="chartworkai_check", arguments=["oops"]))
        responses = served(broken, json.dumps(message("ping", 2)))
        assert responses[0]["error"]["code"] == INVALID_PARAMS
        assert responses[1]["result"] == {}

    def test_a_tool_failure_never_becomes_a_protocol_error(self, project):
        line = json.dumps(
            message(
                "tools/call",
                1,
                name="chartworkai_file_decision",
                arguments={"path": str(project), "title": "t"},
            )
        )
        (response,) = served(line)
        assert "error" not in response
        assert response["result"]["isError"] is True


# --- serve(): a realistic session ---------------------------------------------


class TestFullSession:
    def test_handshake_through_first_tool_call(self, project):
        lines = encoded(
            message("initialize", 1, protocolVersion="2025-06-18", clientInfo={"name": "t"}),
            notification("notifications/initialized"),
            message("tools/list", 2),
            message("tools/call", 3, name="chartworkai_state", arguments={"path": str(project)}),
            message(
                "tools/call",
                4,
                name="chartworkai_file_handoff",
                arguments=arguments_for("chartworkai_file_handoff", project),
            ),
            notification("notifications/cancelled"),
            message("ping", 5),
        )
        responses = served(*lines)

        # Seven messages in, two of them notifications: five lines out.
        assert len(responses) == 5
        assert [r["id"] for r in responses] == [1, 2, 3, 4, 5]
        assert responses[0]["result"]["serverInfo"]["name"] == "chartworkai"
        assert [t["name"] for t in responses[1]["result"]["tools"]] == TOOL_NAMES
        assert json.loads(responses[2]["result"]["content"][0]["text"])["project_root"] == str(
            project.resolve()
        )
        handoff = json.loads(responses[3]["result"]["content"][0]["text"])
        assert (project / handoff["file"]).is_file()
        assert responses[4]["result"] == {}

    def test_a_session_that_writes_then_reads_sees_its_own_writes(self, project):
        write(project, "TASKS.md", "# Tasks\n\n## In Progress\n\n- [ ] work\n")
        lines = encoded(
            message(
                "tools/call",
                1,
                name="chartworkai_file_decision",
                arguments=arguments_for("chartworkai_file_decision", project),
            ),
            message("tools/call", 2, name="chartworkai_state", arguments={"path": str(project)}),
        )
        responses = served(*lines)
        filed = json.loads(responses[0]["result"]["content"][0]["text"])["file"]
        state = json.loads(responses[1]["result"]["content"][0]["text"])
        assert state["recent_decisions"][0]["file"] == filed


# --- End to end through the installed CLI -------------------------------------


def mcp_command() -> List[str]:
    """The ``chartworkai mcp`` entry point, preferring the installed console script."""
    console = Path(sys.executable).parent / "chartworkai"
    if console.is_file():
        return [str(console), "mcp"]
    return [sys.executable, "-m", "chartworkai", "mcp"]


class TestCliSubprocess:
    def test_a_real_handshake_over_a_pipe(self, project):
        stdin = "\n".join(
            encoded(
                message("initialize", 1, protocolVersion="2025-06-18"),
                notification("notifications/initialized"),
                message("tools/list", 2),
                message(
                    "tools/call", 3, name="chartworkai_check", arguments={"path": str(project)}
                ),
            )
        )
        proc = subprocess.run(
            mcp_command(), input=stdin + "\n", capture_output=True, text=True, timeout=60
        )

        assert proc.returncode == 0, proc.stderr
        assert proc.stderr == ""
        responses = [json.loads(line) for line in proc.stdout.splitlines()]
        assert len(responses) == 3  # the notification must not be answered
        assert responses[0]["result"]["serverInfo"] == {
            "name": "chartworkai",
            "version": __version__,
        }
        assert responses[0]["result"]["protocolVersion"] == "2025-06-18"
        assert [t["name"] for t in responses[1]["result"]["tools"]] == TOOL_NAMES
        report = json.loads(responses[2]["result"]["content"][0]["text"])
        assert report["summary"]["ok"] is True
        assert report["tool"] == "chartworkai"


class TestWorkspaceConfinement:
    """Tool paths are confined to the server's workspace.

    An MCP tool argument is chosen by a model acting on text it did not author, so
    an arbitrary path is an injection surface: a poisoned instruction could
    otherwise have the server read or write anywhere the user can.
    """

    @pytest.fixture(autouse=True)
    def _enforce(self, monkeypatch):
        monkeypatch.delenv("CHARTWORKAI_ALLOW_ANY_PATH", raising=False)

    @pytest.mark.parametrize("tool", sorted(TOOLS))
    def test_a_path_outside_the_workspace_is_refused(self, tool, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        outside = tmp_path.parent / "elsewhere"
        outside.mkdir(exist_ok=True)

        arguments = {
            "path": str(outside),
            "title": "t",
            "authority": "a",
            "context": "c",
            "ruling": "r",
            "agent": "x",
            "produced": "p",
            "location": "l",
        }
        response = handle_message(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": tool, "arguments": arguments},
            }
        )
        assert response["result"]["isError"] is True
        payload = json.loads(response["result"]["content"][0]["text"])
        assert "outside this server's workspace" in payload["error"]

    def test_a_path_inside_the_workspace_is_allowed(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        response = handle_message(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "chartworkai_check", "arguments": {"path": "."}},
            }
        )
        assert response["result"]["isError"] is False

    def test_the_escape_hatch_re_enables_outside_paths(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("CHARTWORKAI_ALLOW_ANY_PATH", "1")
        outside = tmp_path.parent / "elsewhere2"
        outside.mkdir(exist_ok=True)
        response = handle_message(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "chartworkai_check", "arguments": {"path": str(outside)}},
            }
        )
        assert response["result"]["isError"] is False
