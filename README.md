# Actionstep MCP server

[![CI](https://github.com/RosenAdvertising/actionstep-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/RosenAdvertising/actionstep-mcp/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP 2026-07-28](https://img.shields.io/badge/MCP-2026--07--28-7C3AED.svg)](https://modelcontextprotocol.io)
[![PyPI version](https://img.shields.io/pypi/v/actionstep-mcp.svg)](https://pypi.org/project/actionstep-mcp/)

Connect Claude and other MCP clients to Actionstep to manage matters, participants, tasks, time and billing.

Actionstep MCP server is a [Model Context Protocol](https://modelcontextprotocol.io) server for [Actionstep](https://actionstep.com), the legal practice management platform. It registers 144 tools that read and write Actionstep data. It runs over stdio by default, for desktop clients such as Claude Desktop, and offers an opt-in stateless Streamable HTTP mode that implements MCP specification 2026-07-28. Actionstep credentials stay on the machine that runs the server: they come from the setup command and your operating system's keyring, never from the client.

## Features

- **Matters**: create, update and list actions (matters), assign participants, move a matter through its workflow steps, and manage its billing settings and rates.
- **Participants**: work with participants, relationships, contact notes, phone records and contact documents.
- **Tasks**: create, update, complete and list tasks, and filter them by matter or assignee.
- **Time and billing**: log time records and time entries, record disbursements, and manage matter rates and billing settings.
- **Calendar**: create, update and delete calendar appointments linked to matters.
- **Communications**: log emails, SMS messages, file notes and scratch notes, and associate emails with matters.
- **Documents**: manage action documents and folders, and read contact documents and folders.
- **Data collections**: read and write custom form data on matters.
- **Webhooks**: create and manage REST hook subscriptions for real-time events.
- **Reference data**: look up action types, participant types, users, roles, divisions, currencies, countries, UTBMS codes and tax codes.

## Tools

The server registers 144 tools.

<details>
<summary>All 144 tools</summary>

- `add_participant_to_action`
- `create_action`
- `create_action_document`
- `create_action_folder`
- `create_action_rate`
- `create_action_type_folder`
- `create_calendar_appointment`
- `create_contact_folder`
- `create_contact_note`
- `create_contact_relationship`
- `create_data_collection_record`
- `create_data_collection_record_value`
- `create_disbursement`
- `create_email`
- `create_email_association`
- `create_file_note`
- `create_participant`
- `create_phone_record`
- `create_quick_code`
- `create_rest_hook`
- `create_scratch_note`
- `create_sms`
- `create_task`
- `create_time_entry`
- `create_time_record`
- `delete_action_document`
- `delete_action_folder`
- `delete_action_rate`
- `delete_action_type_folder`
- `delete_calendar_appointment`
- `delete_contact_document`
- `delete_contact_folder`
- `delete_contact_note`
- `delete_disbursement`
- `delete_email`
- `delete_email_association`
- `delete_file_note`
- `delete_participant`
- `delete_phone_record`
- `delete_rest_hook`
- `delete_scratch_note`
- `delete_task`
- `delete_time_entry`
- `delete_time_record`
- `get_action`
- `get_action_bill_settings`
- `get_action_document`
- `get_action_folder`
- `get_action_participant`
- `get_action_rate`
- `get_action_type`
- `get_action_type_folder`
- `get_calendar_appointment`
- `get_contact_document`
- `get_contact_note`
- `get_contact_relationship`
- `get_current_user`
- `get_data_collection`
- `get_data_collection_record`
- `get_disbursement`
- `get_email`
- `get_file_note`
- `get_participant`
- `get_participant_type`
- `get_phone_record`
- `get_quick_code`
- `get_rest_hook`
- `get_scratch_note`
- `get_sms`
- `get_step`
- `get_task`
- `get_time_entry`
- `get_time_record`
- `get_time_record_activity`
- `get_user`
- `get_utbms_code`
- `list_action_bill_settings`
- `list_action_change_steps`
- `list_action_documents`
- `list_action_folders`
- `list_action_participants`
- `list_action_permissions`
- `list_action_rates`
- `list_action_type_folders`
- `list_action_types`
- `list_actions`
- `list_billing_preferences`
- `list_calendar_appointments`
- `list_contact_documents`
- `list_contact_folders`
- `list_contact_notes`
- `list_contact_relationships`
- `list_countries`
- `list_currencies`
- `list_data_collection_fields`
- `list_data_collection_record_values`
- `list_data_collection_records`
- `list_data_collections`
- `list_disbursements`
- `list_divisions`
- `list_document_templates`
- `list_email_associations`
- `list_emails`
- `list_file_notes`
- `list_participant_relationship_types`
- `list_participant_types`
- `list_participants`
- `list_phone_records`
- `list_quick_codes`
- `list_rates`
- `list_rest_hooks`
- `list_roles`
- `list_scratch_notes`
- `list_settings`
- `list_sms`
- `list_step_tasks`
- `list_steps`
- `list_tags`
- `list_task_templates`
- `list_tasks`
- `list_tax_codes`
- `list_time_entries`
- `list_time_record_activities`
- `list_time_records`
- `list_users`
- `list_utbms_codes`
- `remove_participant_from_action`
- `transition_action_step`
- `update_action`
- `update_action_bill_settings`
- `update_action_folder`
- `update_action_rate`
- `update_calendar_appointment`
- `update_contact_note`
- `update_data_collection_record_value`
- `update_disbursement`
- `update_file_note`
- `update_participant`
- `update_phone_record`
- `update_rest_hook`
- `update_scratch_note`
- `update_task`
- `update_time_entry`
- `update_time_record`

</details>

### Prompts and resources

The server also registers three prompts and three resources.

| Prompt | What it does |
| --- | --- |
| `daily_briefing` | Morning briefing: open actions, overdue tasks, today's calendar and recent time entries. |
| `intake_triage` | Reviews a new matter's participants, tasks, billing settings and documents. Takes `action_id`. |
| `matter_billing_summary` | Summarizes a matter's time entries, disbursements and billing configuration. Takes `action_id`. |

| Resource | What it provides |
| --- | --- |
| `actionstep://action_types` | All action types (matter types) configured in your Actionstep organisation. |
| `actionstep://participant_types` | All participant types (contact roles) such as client, opposing party and witness. |
| `actionstep://security-notes` | Security notes for the server, including webhook destination checks. |

## Requirements

- Python 3.10 or later.
- An Actionstep account with developer credentials (an OAuth client ID and client secret), obtained from the Actionstep developer portal.
- An MCP client such as Claude Desktop.

## Installation

Install [uv](https://docs.astral.sh/uv/), then clone the repository and install its locked dependencies:

```bash
git clone https://github.com/RosenAdvertising/actionstep-mcp.git
cd actionstep-mcp
uv sync --locked
```

Releases are also published to PyPI: `pip install actionstep-mcp` installs version 0.2.0, which predates the HTTP mode described below. Install from source to use HTTP mode.

## Configuration

Run the setup command once. It asks for your Actionstep client ID and client secret, opens a browser for OAuth authorization, and saves the results locally. While you authorize, setup listens on port 8769 and uses `http://127.0.0.1:8769/callback` as the OAuth redirect URI.

```bash
uv run actionstep-mcp-setup
```

Check the connection:

```bash
uv run actionstep-mcp-verify
```

Setup saves the client ID, client secret and API endpoint to your operating system's keyring (see [Credential storage](#credential-storage)) and the OAuth tokens to `~/.actionstep-mcp/tokens.json` with `0600` permissions. Server messages that say to run `actionstep-mcp-setup` mean `uv run actionstep-mcp-setup` from your clone.

The server reads these variables, which you can also set in its environment. The OAuth tokens always come from the setup command, so run it even when you supply the other values through the environment.

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `ACTIONSTEP_CLIENT_ID` | Yes (saved by setup) | Credential store | Actionstep OAuth client ID. |
| `ACTIONSTEP_CLIENT_SECRET` | Yes (saved by setup) | Credential store | Actionstep OAuth client secret. |
| `ACTIONSTEP_API_ENDPOINT` | Yes (saved by setup) | Credential store or the OAuth token file | Your organisation's Actionstep API endpoint (see [Authentication notes](#authentication-notes)). |
| `ACTIONSTEP_MCP_USE_KEYRING` | No | `1` | Set to `0` to skip the operating system keyring and use environment credentials and the file fallback on a headless host. |
| `ACTIONSTEP_ALLOWED_DESTINATION_HOSTS` | No | Unset | Administrator allowlist for webhook destination hosts (see [Webhook destination allowlist](#webhook-destination-allowlist)). |

## Usage with Claude Desktop

Add the server to Claude Desktop's configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "actionstep": {
      "command": "uv",
      "args": ["run", "--locked", "--directory", "/absolute/path/to/actionstep-mcp", "actionstep-mcp"]
    }
  }
}
```

Replace `/absolute/path/to/actionstep-mcp` with the path of your clone, then restart Claude Desktop. Any other stdio MCP client uses the same command and arguments.

## HTTP mode

Stdio is the default. Set `ACTIONSTEP_MCP_TRANSPORT=streamable-http` to serve the stateless Streamable HTTP transport from MCP specification 2026-07-28 at `/mcp`. Each request stands alone: no initialization handshake and no `Mcp-Session-Id`. Clients on earlier protocol versions are served on the same endpoint.

> **Security: this endpoint has no authentication and no TLS.** Anyone who can reach the port can run every tool, including write and delete tools, with this server's vendor credentials. Keep the default loopback bind (`127.0.0.1`), or put the server behind an authenticating TLS proxy on a private network. `ACTIONSTEP_MCP_ALLOWED_HOSTS` and `ACTIONSTEP_MCP_ALLOWED_ORIGINS` protect against browser DNS rebinding, not against direct callers. A proxy in front of it needs connection and idle timeouts: a legacy-style `GET /mcp` with `Accept: text/event-stream` holds a stream open until the client disconnects.

| Variable | Default | Purpose |
| --- | --- | --- |
| `ACTIONSTEP_MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http`. |
| `ACTIONSTEP_MCP_HOST` | `127.0.0.1` | Bind address. `127.0.0.1`, `localhost` and `::1` use the SDK's built-in Host and Origin checks; any other value requires `ACTIONSTEP_MCP_ALLOWED_HOSTS`. |
| `PORT` | `8080` | Port; must be an integer. |
| `ACTIONSTEP_MCP_ALLOWED_HOSTS` | unset | Comma-separated `Host` header values accepted on a non-loopback bind, such as `mcp.example.com:8080` or `mcp.example.com:*`. |
| `ACTIONSTEP_MCP_ALLOWED_ORIGINS` | unset | Comma-separated `Origin` values accepted on a non-loopback bind, such as `https://client.example.com`. Requests without an `Origin` header are accepted. |

Actionstep credentials come from the same configuration as stdio (see [Configuration](#configuration)), never from the request.

```bash
ACTIONSTEP_MCP_TRANSPORT=streamable-http PORT=8080 uv run --locked actionstep-mcp
```

Point the MCP client at `http://127.0.0.1:8080/mcp`. Responses use the SDK's default streaming mode, so a client that disconnects cancels its request.

## Error handling

A failed tool call returns an MCP error result (`isError`) with a fixed message. The server never passes an Actionstep response body, a request URL, a credential or an input value back to the client.

| Situation | What the tool returns |
| --- | --- |
| Setup missing or incomplete | A message telling you to run `actionstep-mcp-setup` (from your clone: `uv run actionstep-mcp-setup`). |
| Authorization expired (HTTP 401, or a failed token refresh) | "Actionstep authorization expired. Run: actionstep-mcp-setup" |
| Access denied (HTTP 403) | "Actionstep access denied: the connected account lacks permission for this action (or the authorization expired; re-run actionstep-mcp-setup if so)." |
| Rate limited (HTTP 429) | "Actionstep rate limit reached. Retry in N seconds." where N comes from the `Retry-After` header. |
| Rejected request (HTTP 400 or 422) | "Actionstep rejected the request. Check the supplied values and try again." |
| Any other HTTP error status | "Actionstep request failed. Check the request and try again." |
| Timeout or connection failure | "Actionstep connection timed out or failed. Check connectivity and retry." Tools that create, update or delete data add that the write outcome is unknown and that you should check whether it completed before retrying. |
| Invalid tool arguments | A message naming the argument and its expected type, such as "Invalid argument 'limit'; expected integer greater than or equal to 1 and less than or equal to 200." |
| Configured API endpoint outside `actionstep.com` or `actionstepstaging.com` | "Invalid Actionstep request values. Check the supplied values and try again." |
| Response that is not valid JSON | "Actionstep returned an unexpected response. Try again or contact support." |
| Anything else | "Actionstep request failed unexpectedly. Check the application log for details." |

Every Actionstep request has a 30-second timeout. On HTTP 429 the server waits for the `Retry-After` interval (10 seconds when the header is missing) and retries, up to 3 times per request and 60 seconds of total waiting per tool call; if the next wait would exceed what is left, the tool returns the rate-limit message at once. On HTTP 401 the server refreshes the OAuth access token once and repeats the request. It does not retry timeouts, connection failures or 5xx responses. A failed resource read returns the same fixed unexpected-error message.

At startup the server exits with a message on stderr and a non-zero status when `ACTIONSTEP_MCP_TRANSPORT` is neither `stdio` nor `streamable-http`, when `PORT` is not an integer, or when a non-loopback `ACTIONSTEP_MCP_HOST` is set without `ACTIONSTEP_MCP_ALLOWED_HOSTS`.

## Credential storage

By default credentials are stored in your operating system's native secret store
via the cross-platform [`keyring`](https://github.com/jaraco/keyring) library:

| OS      | Backend                                  |
| ------- | ---------------------------------------- |
| macOS   | Keychain                                 |
| Windows | Credential Manager                       |
| Linux   | Secret Service (GNOME Keyring / KWallet) |

Secrets saved to keyring use the service name `actionstep-mcp`.

OAuth access and refresh tokens are stored separately in `~/.actionstep-mcp/tokens.json` with `0600` permissions, whichever backend holds the client credentials.

**File fallback.** On a host with no keyring backend (e.g. a headless Linux box
without Secret Service), or if you set `ACTIONSTEP_MCP_USE_KEYRING=0`, credentials
fall back to a `~/.actionstep-mcp/.env` file with `0600` permissions.

On Windows, the file is stored in the user's profile and protected by Windows'
default per-user access rules. On POSIX, files are created with `0600` permissions
and writes fail closed if private permissions cannot be established.

**Read order.** A credential already set in the process environment wins. Otherwise the server reads the OS keyring, then the `.env` file fallback. To make a secret rotated in the keyring take effect, unset `ACTIONSTEP_CLIENT_ID` and `ACTIONSTEP_CLIENT_SECRET` in the shell that starts the server.

## Authentication notes

Actionstep uses a dynamic `api_endpoint`: the URL for your organisation's API is returned in the OAuth token response and varies per firm. The setup wizard captures and stores this automatically.

Configured API endpoints may use any host under `actionstep.com` or `actionstepstaging.com`, including per-organization and regional hosts such as `ap-southeast-2.actionstep.com` (or `actionstepstaging.com` for staging), with no userinfo, query, fragment, or non-default port. Both an origin and the vendor-returned `/api/` base are accepted. See the [Actionstep authentication documentation](https://docs.actionstep.com/authentication).

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

## Webhook destination allowlist

Set `ACTIONSTEP_ALLOWED_DESTINATION_HOSTS` in the server environment, for example `ACTIONSTEP_ALLOWED_DESTINATION_HOSTS=hooks.firm.example,.integrations.firm.example`. Comma-separated exact hosts allow only that host; a leading dot allows the domain and its subdomains. Matching ignores case and trailing dots and normalizes IDNA. An empty or unset list refuses destination URLs before any request. HTTPS, no userinfo, and public literal addresses remain required. This administrator-owned list prevents model-supplied destinations from sending data to arbitrary hosts, including private-address DNS aliases and unapproved redirectors. Approve only hosts whose DNS and redirects the firm trusts; the vendor executes requests later. Tools cannot change this setting.

## Testing

The test suite runs offline and needs no Actionstep account: every Actionstep API call is replaced by an in-process test double, and the tests use fake credentials with keyring access disabled. It covers path-identifier and paging-limit validation, safe error messages, credential and token file handling, webhook destination and API endpoint checks, the setup and verify commands' help output, the stdio server, and the Streamable HTTP transport including the 2026-07-28 wire format, Host and Origin checks and stateless requests.

```bash
uv sync --locked
uv run --locked pytest -q
```

CI runs the suite on every push and pull request to `main`.

## License

MIT. See [LICENSE](LICENSE).
