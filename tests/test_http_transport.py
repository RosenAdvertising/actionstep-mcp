"""Offline coverage for the production stateless HTTP entry point."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager
from unittest.mock import Mock

import httpx
import pytest
from mcp import Client, StdioServerParameters

from actionstep_mcp import __version__, server
from actionstep_mcp.client import ActionstepClient, _active_retry_budget
from tests.test_spec_2026_07_28 import (
    PROTOCOL_VERSION,
    SERVER_INFO_META_KEY,
    _modern_request,
)


@pytest.fixture(autouse=True)
def transport_environment(monkeypatch):
    for variable in (
        "ACTIONSTEP_MCP_TRANSPORT",
        "ACTIONSTEP_MCP_HOST",
        "ACTIONSTEP_MCP_ALLOWED_HOSTS",
        "ACTIONSTEP_MCP_ALLOWED_ORIGINS",
        "PORT",
    ):
        monkeypatch.delenv(variable, raising=False)


@asynccontextmanager
async def http_client():
    app = server.create_serve_app()
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://127.0.0.1:8080",
        ) as client:
            yield client


async def post(client, method, params=None, *, headers=None):
    request_headers, body = _modern_request(method, params)
    request_headers["accept"] = "application/json, text/event-stream"
    request_headers.update(headers or {})
    return await client.post("/mcp", headers=request_headers, json=body)


def result(response):
    assert response.status_code == 200, response.text
    assert "mcp-session-id" not in response.headers
    if response.headers["content-type"].startswith("text/event-stream"):
        payloads = [
            json.loads(line[6:])
            for line in response.text.splitlines()
            if line.startswith("data: ")
        ]
        payload = next(item for item in payloads if item.get("id") == 1)
    else:
        payload = response.json()
    return payload["result"]


def test_http_tools_equal_real_stdio_names_and_schemas():
    async def check():
        env = dict(os.environ, ACTIONSTEP_MCP_TRANSPORT="stdio")
        process = StdioServerParameters(
            command=sys.executable,
            args=["-c", "from actionstep_mcp.server import main; main()"],
            env=env,
        )
        async with Client(process, cache=None) as stdio:
            stdio_tools = (await stdio.list_tools()).tools
        async with http_client() as client:
            http_tools = result(await post(client, "tools/list"))["tools"]
        assert len(http_tools) == 144
        assert {tool["name"]: tool["inputSchema"] for tool in http_tools} == {
            tool.name: tool.input_schema for tool in stdio_tools
        }

    asyncio.run(check())


def test_read_tool_reaches_mocked_vendor_and_ignores_request_credentials(monkeypatch):
    vendor = ActionstepClient.__new__(ActionstepClient)
    vendor.api_endpoint = "https://offline.invalid"
    vendor.session = Mock()
    response = vendor.session.request.return_value
    response.status_code = 200
    response.content = b"mock response"
    expected = {"users": [{"id": 7, "name": "Offline user"}]}
    response.json.return_value = expected
    monkeypatch.setattr(server, "ActionstepClient", lambda: vendor)

    async def check():
        async with http_client() as client:
            return result(
                await post(
                    client,
                    "tools/call",
                    {"name": "list_users", "arguments": {}},
                    headers={"authorization": "Bearer offline-request-token"},
                )
            )

    outcome = asyncio.run(check())
    assert outcome["isError"] is False
    assert json.loads(outcome["content"][0]["text"]) == expected
    vendor.session.request.assert_called_once_with(
        "GET",
        "https://offline.invalid/api/rest/users",
        params=None,
        json=None,
        timeout=30,
    )


def test_two_requests_are_independent_without_session_state(monkeypatch):
    class StubActionstepClient:
        def get_user(self, user_id):
            return {"users": [{"id": user_id}]}

    monkeypatch.setattr(server, "ActionstepClient", StubActionstepClient)

    async def check():
        async with http_client() as client:
            responses = await asyncio.gather(
                *(
                    post(
                        client,
                        "tools/call",
                        {"name": "get_user", "arguments": {"user_id": user_id}},
                        headers={"mcp-session-id": "unrecognized-offline-session"},
                    )
                    for user_id in ("101", "102")
                )
            )
        for response, user_id in zip(responses, ("101", "102")):
            outcome = result(response)
            assert outcome["isError"] is False
            assert json.loads(outcome["content"][0]["text"]) == {
                "users": [{"id": user_id}]
            }

    asyncio.run(check())


def test_stateless_lifespan_runs_once_for_two_requests(monkeypatch):
    events = []

    @asynccontextmanager
    async def lifespan(_server):
        events.append("enter")
        try:
            yield {}
        finally:
            events.append("exit")

    monkeypatch.setattr(server.mcp._lowlevel_server, "lifespan", lifespan)

    async def check():
        async with http_client() as client:
            assert events == ["enter"]
            for _ in range(2):
                result(await post(client, "tools/list"))
            assert events == ["enter"]
        assert events == ["enter", "exit"]

    asyncio.run(check())


@pytest.mark.parametrize("value", [None, "", " STDIO "])
def test_stdio_remains_default_and_runs_existing_call(monkeypatch, value):
    if value is not None:
        monkeypatch.setenv("ACTIONSTEP_MCP_TRANSPORT", value)
    run = Mock()
    monkeypatch.setattr(server.mcp, "run", run)
    assert server._requested_transport() == "stdio"
    server.main()
    run.assert_called_once_with()


def test_unknown_transport_exits_with_both_options(monkeypatch):
    monkeypatch.setenv("ACTIONSTEP_MCP_TRANSPORT", "bogus")
    with pytest.raises(
        SystemExit, match="ACTIONSTEP_MCP_TRANSPORT.*stdio.*streamable-http"
    ):
        server.main()


def test_http_transport_dispatches_and_binds_configured_address(monkeypatch):
    import uvicorn

    monkeypatch.setenv("ACTIONSTEP_MCP_TRANSPORT", " STREAMABLE-HTTP ")
    monkeypatch.setenv("ACTIONSTEP_MCP_HOST", "localhost")
    monkeypatch.setenv("PORT", " 8123 ")
    config = Mock(wraps=uvicorn.Config)
    serve = Mock()

    class StubServer:
        def __init__(self, settings):
            self.settings = settings

        async def serve(self):
            serve()

    monkeypatch.setattr(uvicorn, "Config", config)
    monkeypatch.setattr(uvicorn, "Server", StubServer)
    server.main()
    assert config.call_args.kwargs["host"] == "localhost"
    assert config.call_args.kwargs["port"] == 8123
    assert config.call_args.kwargs["access_log"] is False
    serve.assert_called_once_with()


def test_port_default_and_non_integer_error(monkeypatch):
    assert server._port() == 8080
    assert server._host() == "127.0.0.1"
    monkeypatch.setenv("PORT", "invalid")
    with pytest.raises(SystemExit, match="PORT must be an integer"):
        server._port()


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
def test_loopback_uses_sdk_security(monkeypatch, host):
    monkeypatch.setenv("ACTIONSTEP_MCP_HOST", host)
    assert server._transport_security() is None


@pytest.mark.parametrize("allowed_hosts", [None, "", " , , "])
def test_non_loopback_requires_allowed_hosts(monkeypatch, allowed_hosts):
    monkeypatch.setenv("ACTIONSTEP_MCP_HOST", "0.0.0.0")
    if allowed_hosts is not None:
        monkeypatch.setenv("ACTIONSTEP_MCP_ALLOWED_HOSTS", allowed_hosts)
    with pytest.raises(SystemExit, match="ACTIONSTEP_MCP_ALLOWED_HOSTS"):
        server.create_serve_app()


def test_configured_host_and_origin_validation(monkeypatch):
    monkeypatch.setenv("ACTIONSTEP_MCP_HOST", "0.0.0.0")
    monkeypatch.setenv(
        "ACTIONSTEP_MCP_ALLOWED_HOSTS", " mcp.example:8080, , backup.example "
    )
    monkeypatch.setenv("ACTIONSTEP_MCP_ALLOWED_ORIGINS", " https://app.example, ")

    async def check():
        async with http_client() as client:
            good = {"host": "mcp.example:8080", "origin": "https://app.example"}
            result(await post(client, "tools/list", headers=good))
            bad_host = await post(
                client, "tools/list", headers={"host": "other.example"}
            )
            assert bad_host.status_code == 421
            bad_origin = await post(
                client, "tools/list", headers=dict(good, origin="https://other.example")
            )
            assert bad_origin.status_code == 403

    asyncio.run(check())


def test_loopback_rejects_bad_host_and_origin():
    async def check():
        async with http_client() as client:
            assert (
                await post(client, "tools/list", headers={"host": "other.example"})
            ).status_code == 421
            assert (
                await post(
                    client, "tools/list", headers={"origin": "https://other.example"}
                )
            ).status_code == 403

    asyncio.run(check())


def test_missing_origin_is_allowed_but_unconfigured_origin_is_refused(monkeypatch):
    monkeypatch.setenv("ACTIONSTEP_MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("ACTIONSTEP_MCP_ALLOWED_HOSTS", "127.0.0.1:8080")

    async def check():
        async with http_client() as client:
            result(await post(client, "tools/list"))
            response = await post(
                client, "tools/list", headers={"origin": "https://other.example"}
            )
            assert response.status_code == 403

    asyncio.run(check())


@pytest.mark.parametrize("method", ["GET", "DELETE"])
def test_http_get_and_delete_are_not_allowed(method):
    async def check():
        async with http_client() as client:
            response = await client.request(
                method, "/mcp", headers={"mcp-protocol-version": PROTOCOL_VERSION}
            )
            assert response.status_code == 405
            assert response.headers["allow"] == "POST"
            assert "mcp-session-id" not in response.headers

    asyncio.run(check())


def test_discovery_has_supported_revision_and_package_identity():
    async def check():
        async with http_client() as client:
            return result(await post(client, "server/discover"))

    discovery = asyncio.run(check())
    assert PROTOCOL_VERSION in discovery["supportedVersions"]
    identity = discovery["_meta"][SERVER_INFO_META_KEY]
    assert identity["name"] == "actionstep-mcp"
    assert identity["title"]
    assert identity["version"] == __version__


def test_unknown_tool_remains_an_error_result():
    async def check():
        async with http_client() as client:
            outcome = result(
                await post(
                    client, "tools/call", {"name": "unknown_tool", "arguments": {}}
                )
            )
            assert outcome["isError"] is True

    asyncio.run(check())


def test_tool_cancellation_propagates_and_resets_request_context(monkeypatch):
    async def cancelled(*args):
        raise asyncio.CancelledError

    monkeypatch.setattr(server, "_original_call_tool", cancelled)

    async def check():
        with pytest.raises(asyncio.CancelledError):
            await server._safe_call_tool("create_action", {})
        assert server._active_tool_is_write.get() is False
        assert _active_retry_budget.get() is None

    asyncio.run(check())
