# MCP 2026-07-28 protocol delta

The server targets MCP `2026-07-28` using Python SDK `mcp>=2.2,<3`; `uv.lock`
resolves `mcp` and `mcp-types` to `2.2.0`. The application uses `MCPServer`
and the stdio entry point. The [MCP changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
and [Python SDK migration guide](https://py.sdk.modelcontextprotocol.io/migration/)
describe the protocol and API changes.

| Protocol area | Mapping in this server |
| --- | --- |
| Modern requests and discovery | SDK dispatches requests without MCP session state. `server/discover` advertises the revision, server identity, and tool, resource, and prompt capabilities. Tests also cover legacy negotiation. |
| Result and cache metadata | Discovery, list, and resource results carry `resultType: complete`; SDK list/read defaults use `ttlMs: 0` and `cacheScope: private`. |
| Tools and schemas | Repeated `tools/list` calls retain registration order. SDK-generated object schemas and structured tool results are tested. Paginated tool inputs enforce page and limit bounds. |
| Streamable HTTP routing | In-process raw HTTP tests cover `MCP-Protocol-Version`, `Mcp-Method`, `Mcp-Name`, header mismatch `-32020`, unsupported revision `-32022`, and unknown method `-32601`. Production uses stdio. |
| Resources and subscriptions | Unknown resource URIs return Invalid Params `-32602`. The SDK maps advertised list-change and resource-subscription capabilities; the application has no custom event publisher. |
| Extensions and optional capabilities | No unused extension is advertised. No operation needs an optional client capability, so a `-32021` case is not manufactured. |

MCP authorization, dynamic client registration, sampling, roots, elicitation,
tasks extension, SSE resumption, and server-initiated requests are outside this
application's implemented protocol surface. Actionstep OAuth is downstream
vendor authentication. See [the migration report](SPEC-MIGRATION-REPORT.md)
for reproducible local checks and testing limits.
