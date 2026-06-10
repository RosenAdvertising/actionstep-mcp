#!/usr/bin/env python3
"""One-command OAuth setup for actionstep-mcp.
Opens the browser, captures the callback, exchanges the code, saves tokens + api_endpoint.

Credentials (Client ID, Client Secret, API endpoint) are stored securely via the
OS keyring (macOS Keychain / Windows Credential Manager / Linux Secret Service),
falling back to a 0600 ``.env`` file when no keyring backend is available or
``ACTIONSTEP_MCP_USE_KEYRING=0`` is set.
"""

import json
import os
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

import requests

from actionstep_mcp import credentials

REDIRECT_URI = "http://127.0.0.1:8769/callback"
AUTH_BASE = "https://go.actionstep.com"
AUTH_URL = f"{AUTH_BASE}/oauth/authorize"
TOKEN_URL = f"{AUTH_BASE}/oauth/token"
CONFIG_DIR = Path.home() / ".actionstep-mcp"

_auth_code: str | None = None


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if "code" in params:
            _auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<h2>Authorization complete. You can close this tab.</h2>"
            )
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(
                b"<h2>No code received. Check Actionstep app settings.</h2>"
            )

    def log_message(self, *args):
        pass


def main():
    print("=== actionstep-mcp OAuth Setup ===\n")

    client_id = input("Actionstep Client ID: ").strip()
    client_secret = input("Actionstep Client Secret: ").strip()

    if not client_id or not client_secret:
        print("Error: Client ID and Secret are required.")
        sys.exit(1)

    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid",
    }
    auth_url_full = f"{AUTH_URL}?{urlencode(auth_params)}"

    print("\nOpening browser for Actionstep authorization...")
    print(f"If the browser doesn't open, visit:\n{auth_url_full}\n")
    webbrowser.open(auth_url_full)

    server = HTTPServer(("127.0.0.1", 8769), _CallbackHandler)
    print("Waiting for Actionstep to redirect back (port 8769)...")
    server.handle_request()

    if not _auth_code:
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
        print(f"Token exchange failed ({resp.status_code}): {resp.text}")
        sys.exit(1)

    tokens = resp.json()
    api_endpoint = tokens.get("api_endpoint", "")

    if not api_endpoint:
        print("Warning: api_endpoint not returned in token response.")
        api_endpoint = input("Enter your Actionstep API endpoint URL: ").strip()

    print(f"API endpoint: {api_endpoint}")

    backend = credentials.set_secret("ACTIONSTEP_CLIENT_ID", client_id)
    credentials.set_secret("ACTIONSTEP_CLIENT_SECRET", client_secret)
    credentials.set_secret("ACTIONSTEP_API_ENDPOINT", api_endpoint)

    if backend == "keyring":
        print(
            f"\n✓ Credentials saved to the OS keyring ({credentials.storage_backend()})."
        )
    else:
        print(f"\n✓ Credentials saved to {credentials.ENV_FILE} (0600).")

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    token_file = CONFIG_DIR / "tokens.json"
    with open(token_file, "w") as f:
        json.dump(tokens, f, indent=2)
    os.chmod(token_file, 0o600)

    print(f"✓ Tokens saved to {token_file}")
    print("\nRun 'actionstep-mcp-verify' to test the connection.")


if __name__ == "__main__":
    main()
