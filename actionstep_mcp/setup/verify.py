#!/usr/bin/env python3
"""Post-setup smoke test — verifies auth and basic Actionstep API access."""

import logging
import sys
from pathlib import Path

from actionstep_mcp import credentials

CONFIG_DIR = Path.home() / ".actionstep-mcp"
logger = logging.getLogger(__name__)


def check_config():
    token_file = CONFIG_DIR / "tokens.json"

    credential_keys = (
        "ACTIONSTEP_CLIENT_ID",
        "ACTIONSTEP_CLIENT_SECRET",
        "ACTIONSTEP_API_ENDPOINT",
    )
    if not all(credentials.get_secret(key) for key in credential_keys):
        logger.warning(
            "actionstep_verification_guard_rejected reason=credentials_missing",
            extra={
                "event": "actionstep_verification_guard_rejected",
                "reason": "credentials_missing",
            },
        )
        print("✗ Missing Actionstep credentials")
        print("  Run: actionstep-mcp-setup")
        return False

    if not token_file.exists():
        logger.warning(
            "actionstep_verification_guard_rejected reason=tokens_missing",
            extra={
                "event": "actionstep_verification_guard_rejected",
                "reason": "tokens_missing",
            },
        )
        print("✗ Missing Actionstep tokens")
        print("  Run: actionstep-mcp-setup")
        return False

    print("✓ Credential and token stores found")
    return True


def check_api():
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
        from actionstep_mcp.client import ActionstepClient

        client = ActionstepClient()

        client.get_current_user()
        print("✓ Authentication succeeded")

        actions = client.list_actions(limit=5)
        items = actions.get("actions", []) if isinstance(actions, dict) else actions
        count = len(items) if isinstance(items, list) else 0
        print(f"✓ Actions accessible: {count} returned (limit 5)")

        return True
    except Exception as exc:
        logger.warning(
            "actionstep_verification_failed error_type=%s",
            type(exc).__name__,
            extra={
                "event": "actionstep_verification_failed",
                "error_type": type(exc).__name__,
            },
        )
        print("✗ API check failed. See the PII-free application log for a reason.")
        return False


def main():
    print("=== actionstep-mcp Verification ===\n")
    ok = check_config() and check_api()
    if ok:
        print("\n✓ All checks passed. actionstep-mcp is ready.")
    else:
        print("\n✗ Setup incomplete. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
