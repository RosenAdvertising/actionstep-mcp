#!/usr/bin/env python3
"""Small CI-friendly guard for the repository's MCP protocol target."""

from __future__ import annotations

from mcp.types import LATEST_PROTOCOL_VERSION


EXPECTED_MCP_PROTOCOL_VERSION = "2026-07-28"


def main() -> int:
    if LATEST_PROTOCOL_VERSION != EXPECTED_MCP_PROTOCOL_VERSION:
        print(
            "Spec check: FAIL\n"
            f"Expected {EXPECTED_MCP_PROTOCOL_VERSION}, got {LATEST_PROTOCOL_VERSION}"
        )
        return 1
    print(f"Spec check: PASS ({EXPECTED_MCP_PROTOCOL_VERSION})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
