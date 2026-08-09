# MCP 2026-07-28 migration report

## Result

`actionstep-mcp` now targets MCP `2026-07-28`, up from `2025-11-25`.
The direct Python SDK dependency changed from `mcp>=1.28.1,<2` (locked to
`1.28.1`) to the exact migration release `mcp==2.0.0`. The refreshed lock
contains `mcp-types==2.0.0` and the SDK v2 dependency split.

The authoritative, repository-specific classification and source links are in
[`SPEC-DELTA-2026-07-28.md`](SPEC-DELTA-2026-07-28.md). The implementation
release is identified by the
[official SDK v2.0.0 release notes](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.0.0),
and the code migration follows the
[official v1-to-v2 guide](https://py.sdk.modelcontextprotocol.io/migration/).

No deployment, live Actionstep account, GitHub write, push, or backup repository
was touched.

## Current-revision verdict

This was a migration, not a no-op:

- `pyproject.toml` constrained `mcp>=1.28.1,<2`.
- `uv.lock` resolved `mcp==1.28.1`.
- A clean install from the original lock reported
  `LATEST_PROTOCOL_VERSION == "2025-11-25"`.
- `actionstep_mcp/server.py` constructed the SDK v1 `FastMCP` class.
- The repository had no source tests and no MCP revision guard.

## Implementation

- Replaced `FastMCP` with SDK v2 `MCPServer`, kept the explicit server name,
  added the application version, and retained the existing 144 tools, three
  resources, and three prompts.
- Preserved the bare `mcp.run()` stdio entrypoint. There were no hosted transport
  options to relocate; Streamable HTTP is instantiated only by the offline
  raw-wire tests.
- Kept all existing tool bodies, downstream Actionstep OAuth storage, local
  token state, and cache posture. No MCP session state was introduced.
- Added a lightweight guard that pins `LATEST_PROTOCOL_VERSION` to
  `2026-07-28`.
- Added a core Ruff policy for the declared Python 3.10 floor and changed CI to
  install from the lock and fail on real test failures instead of masking every
  pytest nonzero result as "No tests collected."

## AFFECTS-US mapping

| AFFECTS-US item                                                      | Handling                                                                                                                                                                     | Intended conventional commit                                                       |
| -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Sessionless modern protocol                                          | SDK v2 dispatcher; raw discovery asserts no `Mcp-Session-Id`.                                                                                                                | `feat: migrate server to MCP 2026-07-28`                                           |
| Per-request version/capability metadata and modern handshake removal | Raw modern requests plus modern/legacy `Client` negotiation regressions.                                                                                                     | `feat: migrate server to MCP 2026-07-28`; `test: prove MCP 2026-07-28 conformance` |
| Required `server/discover`                                           | Exact version, identity, capability, cache, and result assertions.                                                                                                           | `test: prove MCP 2026-07-28 conformance`                                           |
| Required `resultType`                                                | Complete-result assertions across discovery, list, read, tool success, and validation error results.                                                                         | `test: prove MCP 2026-07-28 conformance`                                           |
| Modern HTTP routing headers                                          | Raw `MCP-Protocol-Version`, `Mcp-Method`, and `Mcp-Name` requests; method/name mismatch regressions.                                                                         | `test: prove MCP 2026-07-28 conformance`                                           |
| Modern subscription/listen mapping                                   | Preserved SDK-managed list-change and resource-subscription declarations without adding a publisher or bus.                                                                  | `feat: migrate server to MCP 2026-07-28`                                           |
| Capability `extensions` field                                        | Discovery proves no unused extension is advertised.                                                                                                                          | `test: prove MCP 2026-07-28 conformance`                                           |
| Required list/read cache hints                                       | SDK v2 conservative defaults (`ttlMs: 0`, `cacheScope: private`) asserted across tools, prompts, resources, templates, and resource reads.                                   | `test: prove MCP 2026-07-28 conformance`                                           |
| Deterministic `tools/list`                                           | Two independent listings assert the same 144 registered names in the same order.                                                                                             | `test: prove MCP 2026-07-28 conformance`                                           |
| JSON Schema 2020-12 and structured content                           | SDK v2 generated object schemas and structured tool results asserted; bounded list schemas use numeric constraints.                                                          | `feat: migrate server to MCP 2026-07-28`; `test: prove MCP 2026-07-28 conformance` |
| Resource-not-found `-32602`                                          | Unknown resource URI regression asserts Invalid Params.                                                                                                                      | `test: prove MCP 2026-07-28 conformance`                                           |
| Reserved errors                                                      | Header mismatch `-32020`, unsupported version `-32022`, and unknown method `-32601` asserted. No artificial missing-capability operation was added only to trigger `-32021`. | `test: prove MCP 2026-07-28 conformance`                                           |

The delta document belongs to the intended
`docs: document MCP 2026-07-28 delta` commit, and this report belongs to
`docs: report MCP 2026-07-28 migration`. Every intended commit must carry:

```text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
```

## Canary sibling checks

### A. List-tool limit and order — fixed, with one method-only limitation

All 50 exposed `list_*` tools were inspected.

- Twelve tools expose `page` / `limit`. Their schemas now enforce `page >= 1`
  and `1 <= limit <= 200`.
- Each of those twelve performs exactly one upstream GET with the requested
  `page` and `pageSize`; there is no auto-pagination loop that can exceed the
  requested cap. Parameterized tests cover all twelve.
- The other 38 list tools also make one upstream request and do not expose a
  caller limit, so there is no requested total cap for an aggregator to exceed.
- No sort/order parameter existed. The repository has no Actionstep ordering
  contract, and the task's network grant excludes vendor documentation.
  Ordering therefore remains method-verified-only; no guessed vendor parameter
  was added. Some of the 38 unpaginated vendor methods may merit pagination once
  an approved Actionstep support matrix is available.

### B. Silent rejections — fixed

- Webhook URL, OAuth credential/token prerequisite, API response, OAuth callback,
  setup, and verification rejection paths now emit fixed PII-free reason/status
  fields.
- The webhook IP parser no longer inspects exception text. That old pattern
  falsely rejected public DNS names containing `private`, `loopback`, or
  `link-local`; regression tests cover all three.
- No URL, hostname, query, response body, credential, or exception text is
  included in the new logs.

### C. Origin/CSP ceremony — fixed where applicable

The MCP entrypoint is stdio-only, but the setup CLI serves a localhost OAuth GET
callback page. That page now has restrictive CSP, no-store, nosniff, and
no-referrer headers, validates the exact callback path, and binds the callback to
a random constant-time-checked OAuth `state` value.

The Clio `Sec-Fetch-Site: same-origin` fallback is intentionally not applied to
this provider-originated GET callback: a legitimate OAuth top-level navigation
is cross-site and commonly has no `Origin`. The CSP redirect-handoff pattern is
also not applicable because this server never returns an outbound authorization
redirect; navigation starts with `webbrowser.open`.

### D. PII in logs — fixed/clean

- The verification CLI no longer prints the authenticated user's first/last
  name.
- Token/API response bodies and local credential/token paths are no longer
  printed or embedded in raised errors.
- The final source sweep found no `sub`, email, first/last name, URL, hostname,
  credential value, token, or raw response body flowing to an application log.

## Test inventory

### Before

- Original lock install: `mcp==1.28.1`, latest protocol `2025-11-25`.
- `pytest -q`: **0/0 existing tests**; pytest exited 5 because no tests were
  collected.
- Unscoped `ruff check .`: **155 pre-existing findings** because the repository
  had no Ruff policy. The migration adds the same explicit core policy used by
  the pilot.

### After

- Locked install: `mcp==2.0.0`, `mcp-types==2.0.0`, latest protocol
  `2026-07-28`.
- `pytest -q`: **37/37 passed** on Python 3.12.
- `pytest -q`: **37/37 passed** on the declared Python 3.10 floor.
- `ruff check .`: **all checks passed**.
- `git diff --check`: **passed**.
- Seven migration tests cover the guard, discovery, modern/legacy negotiation,
  cache/result semantics, deterministic tools and schemas, resource errors,
  structured tool results, routing headers, and protocol/method errors.
- Sixteen list-control cases cover all twelve bounded schemas, three invalid
  wire inputs, and all twelve single-request client methods.
- Fourteen security cases cover PII-free rejection logging, the hostname parser,
  response-body sanitization, OAuth state/CSP, and verification output.

No live Actionstep smoke test was run. Resource and tool calls that needed data
used offline stubs, and protocol wiring was exercised in memory and over an
in-process raw HTTP transport.

## Git branch and commit limitation

The worktree started clean on default branch `main` at `aee2c06`, exactly
matching `origin/main`. Creating `spec-2026-07-28` failed because the execution
environment grants only read access to this checkout's `.git` administration
directory; Git could not create `.git/index.lock` (`Operation not permitted`).

Consequently, the required branch and four conventional commits could not be
created, and no commit hashes are claimed. The working-tree changes are complete
and tested but remain on `main` as uncommitted changes. No push was attempted.

Current default-branch log:

```text
aee2c06 chore(deps): lock file maintenance (#46)
0341b28 chore(deps): update actions/setup-python action to v7 (#45)
39ba4cc chore(deps): lock file maintenance (#44)
db451a2 chore(deps): lock file maintenance (#43)
6b6db4d chore(deps): update actions/setup-node action to v7 (#42)
379cccc chore(deps): update dependency mcp to >=1.28.1,<2 (#41)
798fb04 chore(deps): update github-actions (#40)
ce1a615 chore(deps): update dependency mcp to v1.28.1 [security] (#39)
```

## Judgment calls and remaining verification

- **Cache policy:** private zero-TTL SDK defaults preserve the existing no-cache
  behavior.
- **Legacy compatibility:** SDK v2 serves modern and 2025-era clients from the
  same server; the test suite proves both.
- **Authorization:** Actionstep OAuth is downstream vendor authentication, not
  MCP transport authorization. The migration preserves its storage model and
  adds only state/log/browser-response hardening required by the canary review.
- **Ordering:** exact Actionstep sort parameters and defaults remain
  method-verified-only because vendor documentation was outside the permitted
  network scope.
- **Live behavior:** no credentialed Actionstep account was used. A repository
  owner should run the existing `actionstep-mcp-verify` command after installing
  from the lock.
