#!/usr/bin/env python3
"""One-command OAuth setup for actionstep-mcp.
Opens the browser, captures the callback, exchanges the code, saves tokens + api_endpoint.

Credentials (Client ID, Client Secret, API endpoint) are stored securely via the
OS keyring (macOS Keychain / Windows Credential Manager / Linux Secret Service),
falling back to a 0600 ``.env`` file when no keyring backend is available or
``ACTIONSTEP_MCP_USE_KEYRING=0`` is set.
"""

import hmac
import json
import logging
import os
import secrets
import sys
import webbrowser
from getpass import getpass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests

from actionstep_mcp import credentials

logger = logging.getLogger(__name__)

REDIRECT_URI = "http://127.0.0.1:8769/callback"
AUTH_BASE = "https://go.actionstep.com"
AUTH_URL = f"{AUTH_BASE}/oauth/authorize"
TOKEN_URL = f"{AUTH_BASE}/oauth/token"
CONFIG_DIR = Path.home() / ".actionstep-mcp"

_auth_code: str | None = None
_expected_state: str | None = None


class _CallbackHandler(BaseHTTPRequestHandler):
    def _send_html(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; "
            "form-action 'none'",
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def _reject(self, reason: str) -> None:
        logger.warning(
            "actionstep_oauth_callback_rejected reason=%s",
            reason,
            extra={
                "event": "actionstep_oauth_callback_rejected",
                "reason": reason,
            },
        )
        self._send_html(
            400,
            b"<h2>Authorization could not be completed. Restart setup.</h2>",
        )

    def do_GET(self):
        global _auth_code, _expected_state
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self._reject("unexpected_callback_path")
            return

        params = parse_qs(parsed.query, keep_blank_values=True)
        supplied_states = params.get("state", [])
        if (
            _expected_state is None
            or len(supplied_states) != 1
            or not hmac.compare_digest(supplied_states[0], _expected_state)
        ):
            self._reject("oauth_state_mismatch")
            return
        if "error" in params:
            self._reject("authorization_provider_error")
            return
        codes = params.get("code", [])
        if len(codes) != 1 or not codes[0]:
            self._reject("authorization_code_missing")
            return

        _auth_code = codes[0]
        _expected_state = None
        self._send_html(
            200, b"<h2>Authorization complete. You can close this tab.</h2>"
        )

    def log_message(self, *args):
        pass


def main():
    global _auth_code, _expected_state
    _auth_code = None
    _expected_state = secrets.token_urlsafe(32)

    print("=== actionstep-mcp OAuth Setup ===\n")

    client_id = input("Actionstep Client ID: ").strip()
    client_secret = getpass("Actionstep Client Secret: ").strip()

    if not client_id or not client_secret:
        logger.warning(
            "actionstep_setup_rejected reason=oauth_client_credentials_missing",
            extra={
                "event": "actionstep_setup_rejected",
                "reason": "oauth_client_credentials_missing",
            },
        )
        print("Error: Client ID and Secret are required.")
        sys.exit(1)

    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid",
        "state": _expected_state,
    }
    auth_url_full = f"{AUTH_URL}?{urlencode(auth_params)}"

    print("\nOpening browser for Actionstep authorization...")
    print(f"If the browser doesn't open, visit:\n{auth_url_full}\n")
    webbrowser.open(auth_url_full)

    server = HTTPServer(("127.0.0.1", 8769), _CallbackHandler)
    print("Waiting for Actionstep to redirect back (port 8769)...")
    server.handle_request()

    if not _auth_code:
        logger.warning(
            "actionstep_setup_rejected reason=authorization_code_missing",
            extra={
                "event": "actionstep_setup_rejected",
                "reason": "authorization_code_missing",
            },
        )
        print("Error: Did not receive authorization code.")
        sys.exit(1)

    print("Exchanging code for tokens...")
    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
            "code": _auth_code,
            "redirect_uri": REDIRECT_URI,
        },
    )

    if resp.status_code != 200:
        logger.warning(
            "actionstep_token_exchange_failed status=%s",
            resp.status_code,
            extra={
                "event": "actionstep_token_exchange_failed",
                "status": resp.status_code,
            },
        )
        print(f"Token exchange failed ({resp.status_code}).")
        sys.exit(1)

    tokens = resp.json()
    api_endpoint = tokens.get("api_endpoint", "")

    if not api_endpoint:
        print("Warning: api_endpoint not returned in token response.")
        api_endpoint = input("Enter your Actionstep API endpoint URL: ").strip()
    if not api_endpoint:
        logger.warning(
            "actionstep_setup_rejected reason=api_endpoint_missing",
            extra={
                "event": "actionstep_setup_rejected",
                "reason": "api_endpoint_missing",
            },
        )
        print("Error: API endpoint is required.")
        sys.exit(1)

    print("API endpoint received.")

    backend = credentials.set_secret("ACTIONSTEP_CLIENT_ID", client_id)
    credentials.set_secret("ACTIONSTEP_CLIENT_SECRET", client_secret)
    credentials.set_secret("ACTIONSTEP_API_ENDPOINT", api_endpoint)

    if backend == "keyring":
        print(
            f"\n✓ Credentials saved to the OS keyring ({credentials.storage_backend()})."
        )
    else:
        print("\n✓ Credentials saved to the protected local file store (0600).")

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    token_file = CONFIG_DIR / "tokens.json"
    with open(token_file, "w") as f:
        json.dump(tokens, f, indent=2)
    os.chmod(token_file, 0o600)

    print("✓ Tokens saved to the protected local token store (0600).")
    print("\nRun 'actionstep-mcp-verify' to test the connection.")


if __name__ == "__main__":
    main()
