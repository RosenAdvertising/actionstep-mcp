# actionstep-mcp

[![PyPI version](https://img.shields.io/pypi/v/actionstep-mcp.svg)](https://pypi.org/project/actionstep-mcp/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MCP server for [Actionstep](https://actionstep.com) — 144 tools covering the full Actionstep REST API for law firm practice management. Use Actionstep from Claude Desktop with natural language.

## What you can do

- **Actions (Matters)** — create, update, assign, track workflow steps, manage billing settings
- **Participants (Contacts)** — full CRUD, relationships, contact notes, phone records
- **Tasks** — create, assign, complete, filter by matter or assignee
- **Time Records & Time Entries** — log time, manage billable entries, activity codes
- **Disbursements** — log expenses, link to matters
- **Calendar** — appointments linked to matters
- **Emails & SMS** — log communications, associate with matters
- **File Notes** — attendance notes and case notes on matters
- **Documents** — action documents and folders
- **Data Collections** — custom form data on matters
- **Webhooks** — REST hook subscriptions for real-time events
- **Reference data** — action types, participant types, rates, UTBMS codes, tax codes

## Requirements

- Python 3.10+
- Python MCP SDK >=2.3,<3 (the protocol target is 2026-07-28)
- Claude Desktop (or any MCP-compatible client)
- Actionstep developer credentials (Client ID, Client Secret)

> **Actionstep developer access:** Register at the Actionstep developer portal to obtain OAuth credentials.

## Installation

```bash
pip install actionstep-mcp
```

## Setup

```bash
actionstep-mcp-setup
```

This opens a browser for OAuth authorization and saves credentials to `~/.actionstep-mcp/`.

Verify:

```bash
actionstep-mcp-verify
```

## Claude Desktop Configuration

```json
{
  "mcpServers": {
    "actionstep": {
      "command": "actionstep-mcp"
    }
  }
}
```

## HTTP mode

Stdio is the default. To serve stateless Streamable HTTP, use these server
environment variables. The MCP endpoint is `/mcp` and supports both the
2026-07-28 protocol and legacy clients through the SDK.

> **Security: this endpoint has no authentication and no TLS.** Anyone who can reach the port can run every tool, including write and delete tools, with this server's vendor credentials. Keep the default loopback bind (`127.0.0.1`), or put the server behind an authenticating TLS proxy on a private network. `ACTIONSTEP_MCP_ALLOWED_HOSTS` and `ACTIONSTEP_MCP_ALLOWED_ORIGINS` protect against browser DNS rebinding, not against direct callers. A proxy in front of it needs connection and idle timeouts: a legacy-style `GET /mcp` with `Accept: text/event-stream` holds a stream open until the client disconnects.

| Variable | Default | Purpose |
| --- | --- | --- |
| `ACTIONSTEP_MCP_TRANSPORT` | `stdio` | Set to `streamable-http` for HTTP. |
| `ACTIONSTEP_MCP_HOST` | `127.0.0.1` | Bind address; SDK protection applies to `127.0.0.1`, `localhost`, and `::1`. |
| `PORT` | `8080` | Integer HTTP port. |
| `ACTIONSTEP_MCP_ALLOWED_HOSTS` | Unset | Required outside the SDK's loopback addresses; comma-separated allowed Host headers, including ports, such as `mcp.example:8080` or `mcp.example:*`. |
| `ACTIONSTEP_MCP_ALLOWED_ORIGINS` | Unset | Optional comma-separated allowed Origins, such as `https://app.example`. Outside loopback, any supplied Origin is refused unless allowed; requests without Origin are accepted. |
| `ACTIONSTEP_CLIENT_ID` | Existing credential store | Actionstep OAuth client ID. |
| `ACTIONSTEP_CLIENT_SECRET` | Existing credential store | Actionstep OAuth client secret. |
| `ACTIONSTEP_API_ENDPOINT` | Existing credential store or OAuth token file | Organisation's Actionstep API endpoint. |
| `ACTIONSTEP_MCP_USE_KEYRING` | `1` | Set to `0` to use environment credentials and file fallback on a headless host. |
| `ACTIONSTEP_ALLOWED_DESTINATION_HOSTS` | Unset | Existing administrator allowlist for webhook destinations (see below). |

After the existing OAuth setup, run:

```bash
ACTIONSTEP_MCP_TRANSPORT=streamable-http PORT=8080 actionstep-mcp
```

Connect the HTTP client to `http://127.0.0.1:8080/mcp`. HTTP uses the same
server-side credentials and OAuth token storage as stdio. Vendor credentials
are never taken from HTTP requests. Responses use the SDK's default streaming
mode so disconnects cancel requests.

## Credential storage

By default credentials are stored in your operating system's native secret store
via the cross-platform [`keyring`](https://github.com/jaraco/keyring) library:

| OS      | Backend                                  |
| ------- | ---------------------------------------- |
| macOS   | Keychain                                 |
| Windows | Credential Manager                       |
| Linux   | Secret Service (GNOME Keyring / KWallet) |

Secrets saved to keyring use the service name `actionstep-mcp`.

**File fallback.** On a host with no keyring backend (e.g. a headless Linux box
without Secret Service), or if you set `ACTIONSTEP_MCP_USE_KEYRING=0`, credentials
fall back to a `~/.actionstep-mcp/.env` file with `0600` permissions.

On Windows, the file is stored in the user's profile and protected by Windows'
default per-user access rules. On POSIX, files are created with `0600` permissions
and writes fail closed if private permissions cannot be established.

**Read order.** Credentials resolve in the order OS keyring → process environment
→ `.env` file. So a rotated secret in the keyring always wins, and an
`ACTIONSTEP_CLIENT_ID` / `ACTIONSTEP_CLIENT_SECRET` exported in your shell overrides
the file fallback without touching the keyring.

## Authentication Notes

Actionstep uses a dynamic `api_endpoint` — the URL for your organisation's API is returned in the OAuth token response and varies per firm. The setup wizard captures and stores this automatically.

## Example usage in Claude

> "List my open actions"
>
> "Create a task on action 456 — send retainer agreement to client"
>
> "Log 2.5 hours on action 789, description: drafted statement of claim"
>
> "Add a file note on action 123 — client called re: mediation date"
>
> "Create a calendar appointment for the Jones hearing on Monday 10am"

## License

MIT

<!-- ci-trigger 2026-05-27 -->

### Approved destination URLs

Set `ACTIONSTEP_ALLOWED_DESTINATION_HOSTS` in the server environment, for example
`ACTIONSTEP_ALLOWED_DESTINATION_HOSTS=hooks.firm.example,.integrations.firm.example`.
Comma-separated exact hosts allow only that host; a leading dot allows the domain
and its subdomains. Matching ignores case and trailing dots and normalizes IDNA.
An empty or unset list refuses destination URLs before any request. HTTPS, no
userinfo, and public literal addresses remain required. This administrator-owned
list prevents model-supplied destinations from sending data to arbitrary hosts,
including private-address DNS aliases and unapproved redirectors. Approve only
hosts whose DNS and redirects the firm trusts; the vendor executes requests later.
Tools cannot change this setting.

Configured API endpoints may use any host under `actionstep.com` or
`actionstepstaging.com`, including per-organization and regional hosts such as
`ap-southeast-2.actionstep.com` (or `actionstepstaging.com` for staging),
with no userinfo, query, fragment, or non-default port. Both an origin and the
vendor-returned `/api/` base are accepted. See the
[Actionstep authentication documentation](https://docs.actionstep.com/authentication).
