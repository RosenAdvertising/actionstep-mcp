"""Safe MCP errors for Actionstep operations."""

from mcp.server.mcpserver.exceptions import ResourceError, ToolError


class SafeToolError(ToolError):
    """An error whose message is safe to return to an MCP client."""


class SafeResourceError(ResourceError):
    """A resource failure with a safe client-facing message."""


SAFE_FALLBACK = (
    "Actionstep request failed unexpectedly. Check the application log for details."
)


def safe_error(exc: Exception, *, write: bool = False) -> SafeToolError:
    """Map known failures to safe, actionable messages and mask everything else."""
    from actionstep_mcp.url_security import UnsafeURL

    from requests import RequestException

    from requests.exceptions import (
        ConnectTimeout,
        ConnectionError,
        ReadTimeout,
        Timeout,
    )

    if isinstance(exc, UnsafeURL):
        return SafeToolError(
            "Webhook target_url must be a public HTTPS URL approved by "
            "ACTIONSTEP_ALLOWED_DESTINATION_HOSTS; configure trusted hostnames."
        )
    if isinstance(exc, SafeToolError):
        return SafeToolError(str(exc))
    if isinstance(exc, ToolError):
        cause = exc.__cause__
        if isinstance(cause, SafeToolError):
            return SafeToolError(str(cause))
        return SafeToolError(SAFE_FALLBACK)
    if isinstance(exc, FileNotFoundError) and "ACTIONSTEP" in str(exc):
        return SafeToolError(
            "Actionstep configuration is missing. Run: actionstep-mcp-setup"
        )
    if isinstance(exc, (ConnectTimeout, ConnectionError, ReadTimeout, Timeout)):
        if write:
            return SafeToolError(
                "Actionstep connection timed out or failed; the write outcome is unknown. "
                "Check whether it completed before retrying."
            )
        return SafeToolError(
            "Actionstep connection timed out or failed. Check connectivity and retry."
        )
    if isinstance(exc, RequestException):
        if write:
            return SafeToolError(
                "Actionstep transport failed; the write outcome is unknown. "
                "Check whether it completed before retrying."
            )
        return SafeToolError(
            "Actionstep transport failed. Check connectivity and retry."
        )
    message = str(exc)
    if message == "ACTIONSTEP_API_ENDPOINT not set. Run: actionstep-mcp-setup":
        return SafeToolError(message)
    if message == "No Actionstep OAuth tokens found. Run: actionstep-mcp-setup":
        return SafeToolError(message)
    if message.startswith(
        "ACTIONSTEP_CLIENT_ID and ACTIONSTEP_CLIENT_SECRET are required"
    ):
        return SafeToolError(
            "Actionstep authorization is incomplete. Run: actionstep-mcp-setup"
        )
    if message.startswith("No refresh token"):
        return SafeToolError(
            "Actionstep authorization expired. Run: actionstep-mcp-setup"
        )
    if message.startswith("Actionstep API error 401") or message.startswith(
        "Token refresh failed (401"
    ):
        return SafeToolError(
            "Actionstep authorization expired. Run: actionstep-mcp-setup"
        )
    if message.startswith("Actionstep API error 403") or message.startswith(
        "Token refresh failed (403"
    ):
        return SafeToolError(
            "Actionstep access denied: the connected account lacks permission for this action "
            "(or the authorization expired; re-run actionstep-mcp-setup if so)."
        )
    if message.startswith("Actionstep API error 429"):
        return SafeToolError(
            "Actionstep rate limit reached. Retry after the time specified by Actionstep."
        )
    if message.startswith("Actionstep API error 400") or message.startswith(
        "Actionstep API error 422"
    ):
        return SafeToolError(
            "Actionstep rejected the request. Check the supplied values and try again."
        )
    if message.startswith("Actionstep API error "):
        return SafeToolError(
            "Actionstep request failed. Check the request and try again."
        )
    if message.startswith("Actionstep API returned a non-JSON response"):
        return SafeToolError(
            "Actionstep returned an unexpected response. Try again or contact support."
        )
    if isinstance(exc, (ValueError, TypeError)):
        return SafeToolError(
            "Invalid Actionstep request values. Check the supplied values and try again."
        )
    return SafeToolError(SAFE_FALLBACK)
