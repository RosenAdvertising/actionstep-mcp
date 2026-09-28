"""Keep offline tests isolated from real Actionstep credential stores."""

from __future__ import annotations

import os


os.environ["ACTIONSTEP_MCP_USE_KEYRING"] = "0"
os.environ["ACTIONSTEP_CLIENT_ID"] = "offline-test-client"
os.environ["ACTIONSTEP_CLIENT_SECRET"] = "offline-test-secret"
os.environ["ACTIONSTEP_API_ENDPOINT"] = "https://offline.invalid"
