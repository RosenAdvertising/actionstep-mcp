"""Daybreak review probes at the registered MCP or real setup/storage boundary."""

import asyncio
import os
import stat
from unittest.mock import Mock

import pytest
from mcp.types import CallToolRequestParams

from actionstep_mcp import client, credentials, server


def invoke(name, arguments):
    return asyncio.run(
        server.mcp._handle_call_tool(
            None, CallToolRequestParams(name=name, arguments=arguments)
        )
    )


def text(result):
    return " ".join(part.text for part in result.content if hasattr(part, "text"))


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("failure", [None, "chmod", "fchmod", "replace"])
def test_setup_secret_file_is_private_and_atomic(
    monkeypatch, tmp_path, existing, failure
):
    target = tmp_path / ".env"
    if existing:
        target.write_text("PROBE=old\n")
        target.chmod(0o644)
    monkeypatch.setattr(credentials, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(credentials, "ENV_FILE", target)
    monkeypatch.setattr(credentials, "_keyring_enabled", lambda: False)

    def save():
        credentials.set_secret("PROBE", "synthetic-value")

    original_open = os.open
    original_replace = os.replace
    seen_modes = []

    def checked_open(path, flags, mode=0o777, *args, **kwargs):
        fd = original_open(path, flags, mode, *args, **kwargs)
        if str(path).endswith(".tmp"):
            seen_modes.append(stat.S_IMODE(os.fstat(fd).st_mode))
            assert mode == 0o600
            assert os.fstat(fd).st_size == 0
        return fd

    def fail(*args, **kwargs):
        raise PermissionError("simulated permission failure")

    def checked_replace(source, dest):
        assert stat.S_IMODE(source.stat().st_mode) == 0o600
        assert "synthetic-value" in source.read_text()
        assert target.read_text() == "PROBE=old\n" if existing else not target.exists()
        return original_replace(source, dest)

    monkeypatch.setattr(os, "open", checked_open)
    monkeypatch.setattr(os, "replace", checked_replace)
    if failure == "chmod":
        monkeypatch.setattr(os, "chmod", fail)
    elif failure == "fchmod":
        monkeypatch.setattr(os, "fchmod", fail)
    elif failure == "replace":
        monkeypatch.setattr(os, "replace", fail)
    previous = os.umask(0o022)
    try:
        if failure in {"fchmod", "replace"}:
            with pytest.raises(PermissionError):
                save()
            assert (
                target.read_text() == "PROBE=old\n" if existing else not target.exists()
            )
        else:
            save()
            assert stat.S_IMODE(target.stat().st_mode) == 0o600
            assert "synthetic-value" in target.read_text()
    finally:
        os.umask(previous)
    assert seen_modes == [0o600]
    assert not list(tmp_path.glob(".*.tmp"))


BAD_URLS = [
    "http://example.com/",
    "file:///tmp/probe",
    "https://user:pass@example.com/",
    "https://127.0.0.1/",
    "https://2130706433/",
    "https://0x7f000001/",
    "https://017700000001/",
    "https://127.1/",
    "https://0177.0.0.1/",
    "https://0x7f.0.0.1/",
    "https://127.0.1/",
    "https://127.0.0.1./",
    "https://%31%32%37.0.0.1/",
    "https://[::1]/",
    "https://[::ffff:127.0.0.1]/",
    "https://[::ffff:7f00:1]/",
    "https://[fe80::1%25en0]/",
    "https://localhost/",
    "https://localhost.localdomain/",
    "https://foo.localhost.localdomain/",
    "https://foo.localhost./",
    "https://LOCALHOST./",
    "https://metadata.google.internal/",
    "https://10.0.0.1/",
    "https://169.254.169.254/",
    "https://100.64.0.1/",
    "https://192.0.2.1/",
    "https://224.0.0.1/",
    "https://240.0.0.1/",
    "https://[2001:db8::1]/",
    "https://[ff02::1]/",
    "https://example.com\\@127.1/",
    "https://example.com:bad/",
    "https://example.com\n/",
    "https://１２７.０.０.１/",
]


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setenv(
        "ACTIONSTEP_ALLOWED_DESTINATION_HOSTS",
        ".example.com,8.8.8.8,2606:4700:4700::1111",
    )
    instance = object.__new__(client.ActionstepClient)
    instance.post = Mock(return_value={"ok": True})
    instance.put = Mock(return_value={"ok": True})
    monkeypatch.setattr(server, "ActionstepClient", lambda: instance)
    return instance


@pytest.mark.parametrize("url", BAD_URLS)
@pytest.mark.parametrize(
    "name,args,key",
    [
        ("create_rest_hook", {"event_name": "probe"}, "target_url"),
        ("update_rest_hook", {"hook_id": "probe"}, "target_url"),
    ],
)
def test_url_probe_rejected_at_mcp(api, name, args, key, url):
    arguments = dict(args)
    arguments[key] = url
    result = invoke(name, arguments)
    assert result.is_error, text(result)
    api.post.assert_not_called()
    api.put.assert_not_called()


@pytest.mark.parametrize(
    "url",
    [
        "https://hooks.example.com/event",
        "https://8.8.8.8/event",
        "https://[2606:4700:4700::1111]/event",
    ],
)
@pytest.mark.parametrize(
    "name,args,key",
    [
        ("create_rest_hook", {"event_name": "probe"}, "target_url"),
        ("update_rest_hook", {"hook_id": "probe"}, "target_url"),
    ],
)
def test_public_destination_reaches_transport(api, name, args, key, url):
    arguments = dict(args)
    arguments[key] = url
    result = invoke(name, arguments)
    assert not result.is_error, text(result)
    assert api.post.called or api.put.called
    assert url in str(api.post.call_args_list + api.put.call_args_list)


BAD_ENDPOINTS = [
    "https://attacker.example",
    "http://ap-southeast-2.actionstep.com",
    "https://x@ap-southeast-2.actionstep.com",
    "https://ap-southeast-2.actionstep.com:444",
    "https://ap-southeast-2.actionstep.com?x",
    "https://ap-southeast-2.actionstep.com#x",
    "https://ap-southeast-2.actionstep.com.attacker.example",
    "https://2130706433",
    "https://ap-southeast-2.actionstep.com/other",
]


@pytest.mark.parametrize("endpoint", BAD_ENDPOINTS)
@pytest.mark.parametrize("source", ["environment", "tokens"])
def test_endpoint_rejected_at_mcp_before_session(monkeypatch, endpoint, source):
    tm = Mock(
        tokens={"api_endpoint": endpoint if source == "tokens" else ""},
        access_token="synthetic-value",
        refresh_token="",
    )
    monkeypatch.setattr(client, "TokenManager", lambda: tm)
    monkeypatch.setattr(
        client, "API_ENDPOINT", endpoint if source == "environment" else ""
    )
    session = Mock(side_effect=AssertionError("no session for unsafe endpoint"))
    monkeypatch.setattr(client.requests, "Session", session)
    result = invoke("get_current_user", {})
    assert result.is_error
    session.assert_not_called()


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://ap-southeast-2.actionstep.com",
        "https://us-east-1.actionstep.com/api/",
        "https://ap-southeast-2.actionstepstaging.com:443/api/",
    ],
)
def test_documented_endpoint_builds_correct_api_path(monkeypatch, endpoint):
    monkeypatch.setattr(
        client,
        "TokenManager",
        lambda: Mock(tokens={}, access_token="synthetic-value", refresh_token=""),
    )
    monkeypatch.setattr(client, "API_ENDPOINT", endpoint)
    instance = client.ActionstepClient()
    assert instance._url("users/current").endswith(".com/api/rest/users/current")
    assert "/api/api/" not in instance._url("users/current")


@pytest.mark.parametrize("manual", [False, True])
def test_setup_rejects_untrusted_api_endpoint(monkeypatch, manual):
    from actionstep_mcp.setup import oauth_flow

    answers = iter(["synthetic-id", "https://attacker.example"])
    monkeypatch.setattr("builtins.input", lambda *a: next(answers))
    monkeypatch.setattr(oauth_flow, "getpass", lambda *a: "synthetic-value")
    monkeypatch.setattr(oauth_flow.webbrowser, "open", lambda *a: None)

    def callback(*args):
        def handle():
            oauth_flow._auth_code = "synthetic-code"

        return Mock(handle_request=handle)

    monkeypatch.setattr(oauth_flow, "HTTPServer", callback)
    response = Mock(status_code=200)
    response.json.return_value = {
        "access_token": "synthetic-value",
        "api_endpoint": "" if manual else "https://attacker.example",
    }
    monkeypatch.setattr(oauth_flow.requests, "post", lambda *a, **kw: response)
    save = Mock()
    monkeypatch.setattr(credentials, "set_secret", save)
    with pytest.raises(SystemExit) as caught:
        oauth_flow._main()
    assert caught.value.code == 1
    save.assert_not_called()
