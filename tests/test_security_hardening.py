"""PII-free rejection logging and localhost OAuth page regressions."""

from __future__ import annotations

import io
import logging

import pytest

from actionstep_mcp import client as client_module
from actionstep_mcp.client import (
    ActionstepClient,
    _json_response,
    _validate_webhook_url,
)
from actionstep_mcp.setup import oauth_flow, verify


@pytest.mark.parametrize(
    ("url", "reason"),
    (
        ("http://public.example/hook", "webhook_non_https_scheme"),
        ("https:///hook", "webhook_missing_hostname"),
        ("https://127.0.0.1/hook", "webhook_private_address"),
        ("https://localhost/hook", "webhook_reserved_hostname"),
    ),
)
def test_webhook_rejections_log_only_fixed_reasons(url, reason, caplog) -> None:
    private_marker = "private-host-marker"
    caplog.set_level(logging.WARNING, logger=client_module.__name__)

    with pytest.raises(ValueError):
        _validate_webhook_url(url + "?marker=" + private_marker)

    record = next(
        record
        for record in caplog.records
        if getattr(record, "event", "") == "actionstep_guard_rejected"
    )
    assert record.reason == reason
    assert private_marker not in caplog.text
    assert url not in caplog.text


@pytest.mark.parametrize(
    "hostname",
    ("private.example.com", "loopback.example.com", "link-local.example.com"),
)
def test_public_dns_names_are_not_misclassified_as_private(hostname) -> None:
    _validate_webhook_url(f"https://{hostname}/hook")


def test_non_json_and_api_errors_do_not_expose_response_bodies(caplog) -> None:
    private_marker = "private-response-body-marker"

    class FakeResponse:
        status_code = 502
        ok = False
        content = private_marker.encode()
        text = private_marker
        headers = {}

        def json(self):
            raise ValueError(private_marker)

    caplog.set_level(logging.WARNING, logger=client_module.__name__)
    with pytest.raises(RuntimeError) as exc_info:
        _json_response(FakeResponse())
    assert private_marker not in str(exc_info.value)
    assert private_marker not in caplog.text

    client = ActionstepClient.__new__(ActionstepClient)
    client.api_endpoint = "https://offline.invalid"
    client.session = MockSession(FakeResponse())  # pyright: ignore[reportAttributeAccessIssue]
    with pytest.raises(RuntimeError) as exc_info:
        client._request("GET", "users", retry=False)
    assert private_marker not in str(exc_info.value)
    assert private_marker not in caplog.text


class MockSession:
    def __init__(self, response):
        self.response = response

    def request(self, *args, **kwargs):
        return self.response


def _callback_handler(path: str):
    handler = oauth_flow._CallbackHandler.__new__(oauth_flow._CallbackHandler)
    handler.path = path
    responses = []
    handler._send_html = lambda status, body: responses.append((status, body))
    return handler, responses


def test_oauth_callback_requires_path_state_and_code(caplog) -> None:
    private_marker = "private-state-marker"
    oauth_flow._auth_code = None
    oauth_flow._expected_state = "expected-state"
    caplog.set_level(logging.WARNING, logger=oauth_flow.__name__)

    handler, responses = _callback_handler(
        f"/callback?code=code-value&state={private_marker}"
    )
    handler.do_GET()

    assert responses[0][0] == 400
    assert oauth_flow._auth_code is None
    record = next(
        record
        for record in caplog.records
        if getattr(record, "event", "") == "actionstep_oauth_callback_rejected"
    )
    assert record.reason == "oauth_state_mismatch"
    assert private_marker not in caplog.text

    oauth_flow._expected_state = "expected-state"
    handler, responses = _callback_handler(
        "/callback?code=code-value&state=expected-state"
    )
    handler.do_GET()
    assert responses[0][0] == 200
    assert oauth_flow._auth_code == "code-value"
    assert oauth_flow._expected_state is None


def test_oauth_callback_html_has_restrictive_security_headers() -> None:
    handler = oauth_flow._CallbackHandler.__new__(oauth_flow._CallbackHandler)
    statuses = []
    headers = {}
    handler.send_response = statuses.append  # pyright: ignore[reportAttributeAccessIssue]
    handler.send_header = headers.__setitem__  # pyright: ignore[reportAttributeAccessIssue]
    handler.end_headers = lambda: None
    handler.wfile = io.BytesIO()

    handler._send_html(200, b"<h2>Complete</h2>")

    assert statuses == [200]
    assert headers["Cache-Control"] == "no-store"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["Referrer-Policy"] == "no-referrer"
    csp = headers["Content-Security-Policy"]
    for directive in (
        "default-src 'none'",
        "frame-ancestors 'none'",
        "base-uri 'none'",
        "form-action 'none'",
    ):
        assert directive in csp


def test_verify_output_does_not_print_authenticated_name(monkeypatch, capsys) -> None:
    private_name = "Private Person Marker"

    class StubClient:
        def get_current_user(self):
            return {"users": [{"firstName": private_name}]}

        def list_actions(self, limit):
            return {"actions": []}

    monkeypatch.setattr(client_module, "ActionstepClient", StubClient)
    assert verify.check_api() is True
    assert private_name not in capsys.readouterr().out


@pytest.mark.parametrize("credentials_present", (False, True))
def test_verify_config_rejections_are_logged_without_paths(
    credentials_present, monkeypatch, tmp_path, capsys, caplog
) -> None:
    private_marker = "private-config-path-marker"
    config_dir = tmp_path / private_marker
    config_dir.mkdir()
    monkeypatch.setattr(verify, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(
        verify.credentials,
        "get_secret",
        lambda _key: "configured" if credentials_present else "",
    )
    caplog.set_level(logging.WARNING, logger=verify.__name__)

    assert verify.check_config() is False

    record = next(
        record
        for record in caplog.records
        if getattr(record, "event", "") == "actionstep_verification_guard_rejected"
    )
    expected_reason = "tokens_missing" if credentials_present else "credentials_missing"
    assert record.reason == expected_reason
    assert private_marker not in caplog.text
    assert private_marker not in capsys.readouterr().out


def test_verify_failure_log_does_not_include_exception_data(
    monkeypatch, capsys, caplog
) -> None:
    private_marker = "private-verification-marker"

    class FailingClient:
        def __init__(self):
            raise RuntimeError(private_marker)

    monkeypatch.setattr(client_module, "ActionstepClient", FailingClient)
    caplog.set_level(logging.WARNING, logger=verify.__name__)

    assert verify.check_api() is False

    record = next(
        record
        for record in caplog.records
        if getattr(record, "event", "") == "actionstep_verification_failed"
    )
    assert record.error_type == "RuntimeError"
    assert private_marker not in caplog.text
    assert private_marker not in capsys.readouterr().out
