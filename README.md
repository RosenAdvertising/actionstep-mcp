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

## Authentication Notes

Actionstep uses a dynamic `api_endpoint` — the URL for your organisation's API is returned in the OAuth token response and varies per firm. The setup wizard captures and stores this automatically.

## Example usage in Claude

> "List my open actions"

> "Create a task on action 456 — send retainer agreement to client"

> "Log 2.5 hours on action 789, description: drafted statement of claim"

> "Add a file note on action 123 — client called re: mediation date"

> "Create a calendar appointment for the Jones hearing on Monday 10am"

## License

MIT
<!-- ci-trigger 2026-05-27 -->