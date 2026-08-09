# MCP specification delta: 2025-11-25 to 2026-07-28

Research date: 2026-08-09. Sources are limited to the official MCP
specification and the official MCP Python SDK documentation and release notes.

## Current target and migration release

This repository currently targets MCP `2025-11-25`:

- `pyproject.toml` declares `mcp>=1.28.1,<2`, and `uv.lock` resolves MCP Python
  SDK `1.28.1`.
- An install from that lock reports `mcp.types.LATEST_PROTOCOL_VERSION` as
  `2025-11-25`.
- `actionstep_mcp/server.py` constructs the v1 `FastMCP` class and uses the
  default stdio transport. There are no protocol tests or spec guard.

The [official changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
says `2026-07-28` follows `2025-11-25`. The implementation release is MCP
Python SDK `2.0.0`; its
[official release notes](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.0.0)
say it supports `2026-07-28` and every earlier revision from the same server.
The code changes below follow the
[official v1-to-v2 migration guide](https://py.sdk.modelcontextprotocol.io/migration/).

Verdicts mean:

- **AFFECTS-US**: this server exposes or relies on the changed surface. The SDK
  may own the wire behavior, but this repository must pin, configure, or test it.
- **NOT-APPLICABLE**: the feature or protocol direction is not implemented here
  and will not be added merely because the revision permits it.

## Protocol negotiation and lifecycle

| Normative change                                                                                                                                                                                                        | Verdict            | Repository-specific reason                                                                                                                                        |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Protocol-level sessions and `Mcp-Session-Id` are removed for modern requests.                                                                                                                                           | **AFFECTS-US**     | The v2 server must serve independent requests without session state. The application already keeps OAuth state outside MCP and the production transport is stdio. |
| Modern requests remove `initialize` / `notifications/initialized` and carry protocol version, client capabilities, and recommended client identity in `_meta`; version mismatch uses `UnsupportedProtocolVersionError`. | **AFFECTS-US**     | SDK v2 supplies the dual-era dispatcher. Tests must exercise self-describing modern requests and retain legacy negotiation.                                       |
| Servers MUST implement `server/discover`.                                                                                                                                                                               | **AFFECTS-US**     | Discovery must advertise `2026-07-28`, the Actionstep server identity, and its actual primitives.                                                                 |
| Every result requires `resultType`, normally `"complete"`.                                                                                                                                                              | **AFFECTS-US**     | Tools, resources, prompts, and discovery all return results.                                                                                                      |
| Server-initiated requests are replaced by Multi Round-Trip Requests (MRTR).                                                                                                                                             | **NOT-APPLICABLE** | No tool, resource, or prompt uses sampling, roots, elicitation, or another server-to-client request.                                                              |
| `ping`, `logging/setLevel`, and `notifications/roots/list_changed` are removed; protocol logging becomes per-request opt-in.                                                                                            | **NOT-APPLICABLE** | The server implements none of these methods and emits no MCP log notifications. Application logs go to stderr.                                                    |

## Transports and notifications

| Normative change                                                                                                                                                 | Verdict            | Repository-specific reason                                                                                                                                                                                |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Streamable HTTP POST requests require `Mcp-Method`, plus `Mcp-Name` for named operations; `x-mcp-header` can project selected tool parameters into HTTP headers. | **AFFECTS-US**     | Production remains stdio, but the SDK-owned HTTP surface is exercised raw on the wire by the fleet conformance suite. No tool opts into `x-mcp-header`.                                                   |
| Standalone HTTP GET and `resources/subscribe` / `resources/unsubscribe` are replaced by `subscriptions/listen`.                                                  | **AFFECTS-US**     | The high-level server advertises SDK-managed prompt/resource/tool list changes and resource subscriptions. SDK v2 maps those declarations; this repository adds no publisher, event store, or custom bus. |
| SSE resumability and redelivery are removed.                                                                                                                     | **NOT-APPLICABLE** | No event store, SSE resumption, or redelivery behavior is configured.                                                                                                                                     |
| Legacy HTTP+SSE is deprecated.                                                                                                                                   | **NOT-APPLICABLE** | The entrypoint exposes stdio, not the legacy SSE transport.                                                                                                                                               |

## Capabilities and extensions

| Normative change                                                                   | Verdict            | Repository-specific reason                                                                                                  |
| ---------------------------------------------------------------------------------- | ------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| `ClientCapabilities` and `ServerCapabilities` gain `extensions`.                   | **AFFECTS-US**     | Discovery exposes the capabilities shape. No extension should be advertised because none is implemented.                    |
| Experimental core tasks move to `io.modelcontextprotocol/tasks`.                   | **NOT-APPLICABLE** | There are no task-protocol handlers; Actionstep task tools are ordinary MCP tools and unrelated to the MCP tasks extension. |
| Roots, Sampling, and Logging are deprecated.                                       | **NOT-APPLICABLE** | None is declared or used.                                                                                                   |
| Sampling `includeContext` values `"thisServer"` and `"allServers"` are deprecated. | **NOT-APPLICABLE** | Sampling is not used.                                                                                                       |

## Tools, resources, prompts, and cache semantics

| Normative change                                                                                                                   | Verdict            | Repository-specific reason                                                                                                                                                      |
| ---------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tools/list`, `prompts/list`, `resources/list`, `resources/templates/list`, and `resources/read` require `ttlMs` and `cacheScope`. | **AFFECTS-US**     | The server exposes 144 tools, three resources, and three prompts. SDK v2's conservative `ttlMs: 0`, `cacheScope: private` defaults preserve the existing no-cache posture.      |
| `tools/list` SHOULD be deterministic.                                                                                              | **AFFECTS-US**     | Registration order is stable and repeated raw listings must return the same 144 names.                                                                                          |
| Tool schemas accept JSON Schema 2020-12 and `structuredContent` may be any JSON value.                                             | **AFFECTS-US**     | Decorators generate input schemas and tool responses. SDK v2 owns the revised models; tests verify object schemas and structured results without widening application behavior. |
| Resource-not-found changes from `-32002` to Invalid Params `-32602`.                                                               | **AFFECTS-US**     | Unknown Actionstep resource URIs must now return `-32602`.                                                                                                                      |
| URL-mode elicitation removes its completion notification and `elicitationId`.                                                      | **NOT-APPLICABLE** | The server performs no elicitation.                                                                                                                                             |
| The generated JSON Schema models minimum, maximum, and default as numbers rather than only integers.                               | **NOT-APPLICABLE** | The repository does not vendor or directly validate against the generated MCP meta-schema; SDK v2 absorbs the correction.                                                       |

## Authorization and security

| Normative change                                                                                             | Verdict            | Repository-specific reason                                                                                                                                                                 |
| ------------------------------------------------------------------------------------------------------------ | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Authorization servers SHOULD return RFC 9207 `iss`, and MCP clients must validate it before code redemption. | **NOT-APPLICABLE** | This MCP server is local stdio and is not an MCP authorization server or MCP OAuth client. Its Actionstep OAuth flow is downstream vendor authentication, not MCP transport authorization. |
| MCP Dynamic Client Registration requires an appropriate `application_type`.                                  | **NOT-APPLICABLE** | The code does not dynamically register an MCP client.                                                                                                                                      |
| Persisted MCP client credentials must be bound to their authorization-server issuer.                         | **NOT-APPLICABLE** | The repository stores Actionstep vendor credentials and tokens, not MCP client registrations.                                                                                              |
| Dynamic Client Registration is deprecated in favor of Client ID Metadata Documents.                          | **NOT-APPLICABLE** | The server neither hosts DCR nor acts as a dynamically registered MCP client.                                                                                                              |

## Errors, metadata, and observability

| Normative change                                                                                                                                                 | Verdict            | Repository-specific reason                                                                                                                                                                    |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| MCP reserves `-32020..-32099`; header mismatch, missing capability, and unsupported protocol use `-32020`, `-32021`, and `-32022`; unknown methods use `-32601`. | **AFFECTS-US**     | Raw HTTP conformance tests cover header mismatch, unsupported version, and unknown method. There is no operation requiring a new optional client capability, so `-32021` is not manufactured. |
| `_meta` formally carries W3C `traceparent`, `tracestate`, and `baggage`.                                                                                         | **NOT-APPLICABLE** | The repository has no MCP `_meta` tracing integration. SDK propagation does not require an application feature.                                                                               |

Governance and SEP workflow changes are omitted because they impose no runtime
wire or server requirement. The feature lifecycle is respected by not adopting
deprecated Roots, Sampling, Logging, HTTP+SSE, or DCR.
