"""Round 2 policy regressions through registered MCP calls, with mocked transport."""

import pytest
from .test_daybreak_security import api as api
from .test_daybreak_security import invoke, text, BAD_URLS

SETTING = "ACTIONSTEP_ALLOWED_DESTINATION_HOSTS"


@pytest.mark.parametrize(
    "name,args,key",
    [
        ("create_rest_hook", {"event_name": "probe"}, "target_url"),
        ("update_rest_hook", {"hook_id": "probe"}, "target_url"),
    ],
)
@pytest.mark.parametrize(
    "url",
    BAD_URLS
    + [
        "https://127.0.0.1.sslip.io/",
        "https://example.com/redirect?next=http%3A%2F%2F127.0.0.1%2F",
        "https://unlisted.example/",
        "https://hooks.firm.example.attacker.example/",
        "https://nothooks.firm.example/",
    ],
)
def test_unapproved_destination_zero_requests(api, monkeypatch, name, args, key, url):
    monkeypatch.setenv(SETTING, "hooks.firm.example")
    arguments = dict(args)
    arguments[key] = url
    result = invoke(name, arguments)
    assert result.is_error, text(result)
    api.post.assert_not_called()
    api.put.assert_not_called()


@pytest.mark.parametrize(
    "name,args,key",
    [
        ("create_rest_hook", {"event_name": "probe"}, "target_url"),
        ("update_rest_hook", {"hook_id": "probe"}, "target_url"),
    ],
)
@pytest.mark.parametrize("setting", [None, "", " , "])
def test_missing_allowlist_actionable_zero_requests(
    api, monkeypatch, name, args, key, setting
):
    if setting is None:
        monkeypatch.delenv(SETTING, raising=False)
    else:
        monkeypatch.setenv(SETTING, setting)
    url = "https://hooks.firm.example/event"
    arguments = dict(args)
    arguments[key] = url
    result = invoke(name, arguments)
    assert result.is_error, text(result)
    assert SETTING in text(result)
    api.post.assert_not_called()
    api.put.assert_not_called()


@pytest.mark.parametrize(
    "name,args,key",
    [
        ("create_rest_hook", {"event_name": "probe"}, "target_url"),
        ("update_rest_hook", {"hook_id": "probe"}, "target_url"),
    ],
)
@pytest.mark.parametrize(
    "setting,url",
    [
        ("hooks.firm.example", "https://hooks.firm.example/event"),
        (
            " unrelated.example, HOOKS.FIRM.EXAMPLE. ",
            "https://HOOKS.FIRM.EXAMPLE./event",
        ),
        (".firm.example", "https://firm.example/event"),
        (".firm.example", "https://sub.hooks.firm.example/event"),
        ("bücher.example", "https://xn--bcher-kva.example/event"),
        ("xn--bcher-kva.example", "https://bücher.example/event"),
    ],
)
def test_approved_destination_preserved(
    api, monkeypatch, name, args, key, setting, url
):
    monkeypatch.setenv(SETTING, setting)
    arguments = dict(args)
    arguments[key] = url
    result = invoke(name, arguments)
    assert not result.is_error, text(result)
    assert api.post.called or api.put.called
    assert url in str(api.post.call_args_list + api.put.call_args_list)


@pytest.mark.parametrize(
    "name,args,key",
    [
        ("create_rest_hook", {"event_name": "probe"}, "target_url"),
        ("update_rest_hook", {"hook_id": "probe"}, "target_url"),
    ],
)
@pytest.mark.parametrize(
    "setting,url",
    [
        ("firm.example", "https://sub.firm.example/"),
        (".firm.example", "https://notfirm.example/"),
        (".firm.example", "https://firm.example.attacker.example/"),
        ("*", "https://hooks.firm.example/"),
        ("https://hooks.firm.example", "https://hooks.firm.example/"),
        ("hooks.firm.example/path", "https://hooks.firm.example/"),
        ("hooks.firm.example:443", "https://hooks.firm.example/"),
    ],
)
def test_allowlist_is_exact_and_fail_closed(
    api, monkeypatch, name, args, key, setting, url
):
    monkeypatch.setenv(SETTING, setting)
    arguments = dict(args)
    arguments[key] = url
    result = invoke(name, arguments)
    assert result.is_error, text(result)
    api.post.assert_not_called()
    api.put.assert_not_called()


@pytest.mark.parametrize(
    "name,args,key",
    [
        ("create_rest_hook", {"event_name": "probe"}, "target_url"),
        ("update_rest_hook", {"hook_id": "probe"}, "target_url"),
    ],
)
@pytest.mark.parametrize(
    "setting,url",
    [
        (None, "https://hooks.firm.example/"),
        ("hooks.firm.example", "https://127.0.0.1.sslip.io/"),
        (
            "hooks.firm.example",
            "https://example.com/redirect?next=http%3A%2F%2F127.0.0.1%2F",
        ),
    ],
)
def test_rejection_precedes_client_construction(
    monkeypatch, name, args, key, setting, url
):
    from unittest.mock import Mock
    from actionstep_mcp import server

    factory = Mock(side_effect=AssertionError("no client or token refresh"))
    monkeypatch.setattr(server, "ActionstepClient", factory)
    if setting is None:
        monkeypatch.delenv(SETTING, raising=False)
    else:
        monkeypatch.setenv(SETTING, setting)
    arguments = dict(args)
    arguments[key] = url
    assert invoke(name, arguments).is_error
    factory.assert_not_called()


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://ap-southeast-2.actionstep.com",
        "https://us-east-1.actionstep.com/api/",
        "https://your-org.actionstep.com",
        "https://api.actionstep.com",
        "https://region.firm.actionstep.com/api",
        "https://AP-SOUTHEAST-2.ACTIONSTEP.COM/api/",
        "https://actionstep.com",
        "https://actionstepstaging.com",
        "https://your-org.actionstepstaging.com/api/",
        "https://ap-southeast-2.actionstepstaging.com:443/api/",
    ],
)
@pytest.mark.parametrize("source", ["environment", "tokens"])
def test_vendor_endpoint_shapes_at_mcp(monkeypatch, endpoint, source):
    from unittest.mock import Mock
    from actionstep_mcp import client
    from urllib.parse import urlsplit

    tm = Mock(
        tokens={"api_endpoint": endpoint if source == "tokens" else ""},
        access_token="synthetic-value",
        refresh_token="",
    )
    monkeypatch.setattr(client, "TokenManager", lambda: tm)
    monkeypatch.setattr(
        client, "API_ENDPOINT", endpoint if source == "environment" else ""
    )
    response = Mock(status_code=200, headers={}, ok=True)
    response.json.return_value = {"ok": True}
    session = Mock()
    session.request.return_value = response
    monkeypatch.setattr(client.requests, "Session", lambda: session)
    result = invoke("get_current_user", {})
    assert not result.is_error, text(result)
    assert session.request.call_args.args[1] == (
        "https://" + urlsplit(endpoint).hostname + "/api/rest/users/current"
    )
