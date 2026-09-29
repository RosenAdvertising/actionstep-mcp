from __future__ import annotations

import asyncio
import stat

import pytest
import requests

from actionstep_mcp import client as client_module, server
from actionstep_mcp.client import ActionstepClient, TokenManager
from actionstep_mcp.errors import SAFE_FALLBACK
from actionstep_mcp.setup import oauth_flow, verify
from tests.test_spec_2026_07_28 import _post_modern, _result


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            RuntimeError("ACTIONSTEP_API_ENDPOINT not set. Run: actionstep-mcp-setup"),
            "ACTIONSTEP_API_ENDPOINT not set. Run: actionstep-mcp-setup",
        ),
        (
            RuntimeError("Actionstep API error 401"),
            "Actionstep authorization expired. Run: actionstep-mcp-setup",
        ),
        (
            RuntimeError("Actionstep API error 403"),
            "Actionstep access denied: the connected account lacks permission for this action (or the authorization expired; re-run actionstep-mcp-setup if so).",
        ),
        (
            RuntimeError("Actionstep API error 429"),
            "Actionstep rate limit reached. Retry after the time specified by Actionstep.",
        ),
        (
            requests.Timeout("secret.invalid?token=sentinel"),
            "Actionstep connection timed out or failed. Check connectivity and retry.",
        ),
        (
            requests.ConnectionError("secret.invalid?token=sentinel"),
            "Actionstep connection timed out or failed. Check connectivity and retry.",
        ),
        (RuntimeError("secret.invalid?token=sentinel"), SAFE_FALLBACK),
    ],
)
def test_tool_failures_have_safe_exact_text_and_is_error(monkeypatch, error, expected):
    class BrokenClient:
        def get_current_user(self):
            raise error

    monkeypatch.setattr(server, "ActionstepClient", BrokenClient)
    response = asyncio.run(
        _post_modern("tools/call", {"name": "get_current_user", "arguments": {}})
    )
    result = _result(response)
    assert result["isError"] is True
    assert result["content"][0]["text"] == expected
    assert "sentinel" not in result["content"][0]["text"]


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
@pytest.mark.parametrize("failure", [requests.Timeout, requests.ConnectionError])
def test_write_transport_errors_warn_unknown_outcome(method, failure):
    client = ActionstepClient.__new__(ActionstepClient)

    class BrokenSession:
        def request(self, *args, **kwargs):
            raise failure("secret host sentinel")

    client.api_endpoint = "https://offline.invalid"
    client.session = BrokenSession()
    with pytest.raises(Exception) as exc:
        client._request(method, "actions/1")
    assert str(exc.value) == (
        "Actionstep connection timed out or failed; the write outcome is unknown. "
        "Check whether it completed before retrying."
    )


def test_write_timeout_has_unknown_outcome_and_is_error(monkeypatch):
    class BrokenClient:
        def create_action(self, *args, **kwargs):
            raise requests.Timeout("secret host sentinel")

    monkeypatch.setattr(server, "ActionstepClient", BrokenClient)
    response = asyncio.run(
        _post_modern(
            "tools/call",
            {
                "name": "create_action",
                "arguments": {"name": "Matter", "action_type_id": "1"},
            },
        )
    )
    result = _result(response)
    assert result["isError"] is True
    assert result["content"][0]["text"] == (
        "Actionstep connection timed out or failed; the write outcome is unknown. "
        "Check whether it completed before retrying."
    )
    assert "sentinel" not in result["content"][0]["text"]


def test_request_timeout_and_path_segment_escaping():
    client = ActionstepClient.__new__(ActionstepClient)
    client.api_endpoint = "https://offline.invalid"

    class Response:
        status_code = 200
        ok = True
        content = b'{"actions": []}'
        headers = {}

        @staticmethod
        def json():
            return {"actions": []}

    class Session:
        headers = {}

        def request(self, method, url, **kwargs):
            self.seen = (method, url, kwargs)
            return Response()

    client.session = Session()
    client.get_action("../x?#/y")
    assert (
        client.session.seen[1]
        == "https://offline.invalid/api/rest/actions/..%2Fx%3F%23%2Fy"
    )
    assert client.session.seen[2]["timeout"] == 30


def test_retry_after_uses_total_budget_without_shortening_vendor_delay(monkeypatch):
    client = ActionstepClient.__new__(ActionstepClient)
    client.api_endpoint = "https://offline.invalid"

    class Response:
        status_code = 429
        ok = False
        content = b"{}"
        headers = {"Retry-After": "61"}

    class Session:
        def request(self, *args, **kwargs):
            return Response()

    client.session = Session()
    with pytest.raises(Exception, match="Retry in 61 seconds"):
        client._request("GET", "users")


def test_retry_after_aggregate_budget_across_requests(monkeypatch):
    client = ActionstepClient.__new__(ActionstepClient)
    client.api_endpoint = "https://offline.invalid"
    now = [0]
    sleeps = []
    monkeypatch.setattr(client_module.time, "monotonic", lambda: now[0])

    def sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    monkeypatch.setattr(client_module.time, "sleep", sleep)

    class Response:
        status_code = 429
        ok = False
        content = b"{}"
        headers = {"Retry-After": "40"}

    class Session:
        def request(self, *args, **kwargs):
            return Response()

    client.session = Session()
    with pytest.raises(Exception, match="Retry in 40 seconds"):
        client._request("GET", "users")
    assert sleeps == [40]


def test_verify_entrypoint_bad_key_reports_safe_authorization_guidance(
    monkeypatch, capsys, tmp_path
):
    monkeypatch.setattr(verify.credentials, "get_secret", lambda key: "fake-key")
    (tmp_path / "tokens.json").write_text("{}")
    monkeypatch.setattr(verify, "CONFIG_DIR", tmp_path)

    class BadKeyClient:
        def __init__(self):
            raise RuntimeError(
                "Actionstep API error 401: secret.invalid/token=sentinel"
            )

    monkeypatch.setattr("actionstep_mcp.client.ActionstepClient", BadKeyClient)
    # check_api imports ActionstepClient lazily from the client module.
    with pytest.raises(SystemExit) as exc:
        verify.main()
    assert exc.value.code == 1
    output = capsys.readouterr().out
    assert "authorization expired" in output
    assert "sentinel" not in output
    assert "Traceback" not in output


def test_token_file_created_private_from_initial_open(tmp_path, monkeypatch):
    monkeypatch.setattr(client_module, "CONFIG_DIR", tmp_path)
    manager = TokenManager()
    manager.save({"access_token": "fake"})
    assert stat.S_IMODE(manager.token_file.stat().st_mode) == 0o600


@pytest.mark.parametrize("input_mode", ["eof", "empty"])
def test_setup_entrypoint_incomplete_input_is_actionable_without_traceback(
    monkeypatch, capsys, input_mode
):
    if input_mode == "eof":
        monkeypatch.setattr(
            "builtins.input", lambda _: (_ for _ in ()).throw(EOFError())
        )
    else:
        monkeypatch.setattr("builtins.input", lambda _: "")
        monkeypatch.setattr(oauth_flow, "getpass", lambda _: "")
    with pytest.raises(SystemExit) as exc:
        oauth_flow.main()
    assert exc.value.code == 1
    output = capsys.readouterr().out
    assert (
        "input ended" if input_mode == "eof" else "Client ID and Secret are required"
    ) in output
    assert "Traceback" not in output


def test_setup_entrypoint_fake_rejected_key_has_safe_output(
    monkeypatch, capsys, tmp_path
):
    monkeypatch.setattr(oauth_flow, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr("builtins.input", lambda _: "fake-client-id")
    monkeypatch.setattr(oauth_flow, "getpass", lambda _: "fake-secret-sentinel")
    monkeypatch.setattr(oauth_flow.webbrowser, "open", lambda _: True)

    class FakeServer:
        timeout = None

        def __init__(self, *args, **kwargs):
            pass

        def handle_request(self):
            oauth_flow._auth_code = "fake-code"

    class FakeResponse:
        status_code = 401

    monkeypatch.setattr(oauth_flow, "HTTPServer", FakeServer)
    monkeypatch.setattr(
        oauth_flow.requests, "post", lambda *args, **kwargs: FakeResponse()
    )
    with pytest.raises(SystemExit) as exc:
        oauth_flow.main()
    assert exc.value.code == 1
    output = capsys.readouterr().out
    assert "Token exchange failed (401)" in output
    assert "fake-secret-sentinel" not in output
    assert "Traceback" not in output


def test_verify_entrypoint_missing_config_exits_clearly(monkeypatch, capsys):
    monkeypatch.setattr(verify.credentials, "get_secret", lambda key: "")
    with pytest.raises(SystemExit) as exc:
        verify.main()
    assert exc.value.code == 1
    output = capsys.readouterr().out
    assert "Missing Actionstep credentials" in output
    assert "Traceback" not in output


def test_validation_reports_safe_shape_without_rejected_value():
    response = asyncio.run(
        _post_modern(
            "tools/call",
            {"name": "list_actions", "arguments": {"limit": "PRIVATE_VALUE"}},
        )
    )
    result = _result(response)
    assert result["isError"] is True
    assert (
        result["content"][0]["text"]
        == "Invalid argument 'limit'; expected integer greater than or equal to 1 and less than or equal to 200."
    )


def test_arbitrary_tool_error_cannot_impersonate_safe_rate_limit(monkeypatch):
    from mcp.server.mcpserver.exceptions import ToolError

    class BrokenClient:
        def get_current_user(self):
            raise ToolError("Actionstep rate limit reached. Retry in PRIVATE_VALUE")

    monkeypatch.setattr(server, "ActionstepClient", BrokenClient)
    result = _result(
        asyncio.run(
            _post_modern("tools/call", {"name": "get_current_user", "arguments": {}})
        )
    )
    assert result["isError"] is True
    assert result["content"][0]["text"] == SAFE_FALLBACK


def test_oauth_403_has_permission_guidance():
    from actionstep_mcp.errors import safe_error

    assert str(safe_error(RuntimeError("Token refresh failed (403)"))) == (
        "Actionstep access denied: the connected account lacks permission for this action "
        "(or the authorization expired; re-run actionstep-mcp-setup if so)."
    )


def test_fallback_credential_file_is_private_at_creation(tmp_path, monkeypatch):
    from actionstep_mcp import credentials

    monkeypatch.setattr(credentials, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(credentials, "ENV_FILE", tmp_path / ".env")
    credentials._write_env_file({"ACTIONSTEP_CLIENT_ID": "fake-client"})
    assert stat.S_IMODE((tmp_path / ".env").stat().st_mode) == 0o600
