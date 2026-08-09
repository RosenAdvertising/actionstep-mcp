"""Canary regressions for list limits and upstream pagination behavior."""

from __future__ import annotations

import asyncio
from unittest.mock import Mock

import pytest

from actionstep_mcp import server
from actionstep_mcp.client import ActionstepClient
from tests.test_spec_2026_07_28 import _post_modern, _result


PAGINATED_LIST_TOOLS = (
    "list_actions",
    "list_participants",
    "list_phone_records",
    "list_tasks",
    "list_file_notes",
    "list_scratch_notes",
    "list_time_records",
    "list_time_entries",
    "list_disbursements",
    "list_calendar_appointments",
    "list_emails",
    "list_sms",
)


def test_every_paginated_list_tool_has_schema_enforced_bounds() -> None:
    result = _result(asyncio.run(_post_modern("tools/list")))
    schemas = {tool["name"]: tool["inputSchema"] for tool in result["tools"]}

    assert set(PAGINATED_LIST_TOOLS) <= schemas.keys()
    for name in PAGINATED_LIST_TOOLS:
        properties = schemas[name]["properties"]
        assert properties["limit"]["minimum"] == 1
        assert properties["limit"]["maximum"] == 200
        assert properties["page"]["minimum"] == 1


@pytest.mark.parametrize(
    "arguments",
    (
        {"limit": 0},
        {"limit": 201},
        {"page": 0},
    ),
)
def test_invalid_list_bounds_are_rejected_before_vendor_access(
    arguments, monkeypatch
) -> None:
    client = Mock(side_effect=AssertionError("vendor client must not be constructed"))
    monkeypatch.setattr(server, "ActionstepClient", client)
    result = _result(
        asyncio.run(
            _post_modern(
                "tools/call",
                {"name": "list_actions", "arguments": arguments},
            )
        )
    )
    assert result["isError"] is True
    assert result["resultType"] == "complete"
    client.assert_not_called()


@pytest.mark.parametrize("method_name", PAGINATED_LIST_TOOLS)
def test_each_paginated_client_method_makes_one_capped_request(method_name) -> None:
    client = ActionstepClient.__new__(ActionstepClient)
    client.get = Mock(return_value={})

    getattr(client, method_name)(page=3, limit=7)

    client.get.assert_called_once()
    params = client.get.call_args.args[1]
    assert params["page"] == 3
    assert params["pageSize"] == 7
