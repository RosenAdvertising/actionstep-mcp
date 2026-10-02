# MCP 2026-07-28 migration

This server targets MCP protocol revision `2026-07-28` through the Python SDK
requirement `mcp>=2.2,<3`. The lock resolves `mcp` and `mcp-types` to `2.2.0`.
The server uses `MCPServer("actionstep-mcp", version="0.1.0", ...)` and runs
over stdio. Its registered application surface has 144 tools, three resources,
and three prompts. [The delta notes](SPEC-DELTA-2026-07-28.md) map the protocol
changes to this server.

## Application behavior

- The SDK handles modern discovery, request metadata, result types, cache hints,
  routing errors, and legacy client negotiation. The protocol tests exercise
  these through in-process transports, including raw Streamable HTTP requests.
  The application entry point remains stdio.
- The existing Actionstep OAuth and credential storage are downstream vendor
  authentication. The migration adds no MCP transport authorization, session
  store, subscription publisher, or outbound HTTP deployment.
- Paginated list tools validate `page >= 1` and `1 <= limit <= 200`; each
  corresponding client method makes one upstream request with `page` and
  `pageSize`. Other list tools do not expose a caller limit. Vendor ordering and
  live pagination behavior require validation against Actionstep.
- Webhook URL validation rejects non-HTTPS, private, loopback, link-local, and
  reserved destinations. Rejection logs use fixed reason fields. The local
  OAuth callback validates path and state and sends restrictive response
  headers. Verification output omits the authenticated person's name.

## Reproduce local validation

Run from the repository root with the locked development environment and Ruff
installed.
The test settings use fake credentials, disable keyring access, and direct any
accidental endpoint use to an invalid domain. Tests mock vendor calls; they do
not exercise a live Actionstep account.

```bash
env ACTIONSTEP_MCP_USE_KEYRING=0 ACTIONSTEP_CLIENT_ID=offline-test-client ACTIONSTEP_CLIENT_SECRET=offline-test-secret ACTIONSTEP_API_ENDPOINT=https://offline.invalid PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
env ACTIONSTEP_MCP_USE_KEYRING=0 ACTIONSTEP_CLIENT_ID=offline-test-client ACTIONSTEP_CLIENT_SECRET=offline-test-secret ACTIONSTEP_API_ENDPOINT=https://offline.invalid PYTHONDONTWRITEBYTECODE=1 .venv/bin/python tests/spec_check.py
ruff check --no-cache actionstep_mcp tests
uv lock --check --offline
```

## Error behavior

Tool failures use safe, actionable `ToolError` messages for recognized
configuration, authorization, HTTP, rate-limit, validation, and transport
conditions. Unexpected failures use a fixed masked message. Unexpected
resource failures are masked before reaching the client or SDK logs, without
logging the underlying exception or traceback. API response bodies, request URLs,
credentials, and input values are not included in tool error messages.

The checks above cover local, mocked behavior. Live Actionstep OAuth, API
responses, vendor ordering, and hosted runtime behavior remain unverified.
