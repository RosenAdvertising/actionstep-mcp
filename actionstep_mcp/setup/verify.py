#!/usr/bin/env python3
"""Post-setup smoke test — verifies auth and basic Actionstep API access."""

import sys
from pathlib import Path

CONFIG_DIR = Path.home() / ".actionstep-mcp"


def check_config():
    env_file = CONFIG_DIR / ".env"
    token_file = CONFIG_DIR / "tokens.json"

    if not env_file.exists():
        print(f"✗ Missing credentials: {env_file}")
        print("  Run: actionstep-mcp-setup")
        return False

    if not token_file.exists():
        print(f"✗ Missing tokens: {token_file}")
        print("  Run: actionstep-mcp-setup")
        return False

    print(f"✓ Config found: {CONFIG_DIR}")
    return True


def check_api():
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
        from actionstep_mcp.client import ActionstepClient

        client = ActionstepClient()

        user = client.get_current_user()
        users = user.get("users", user)
        if isinstance(users, list) and users:
            users = users[0]
        if isinstance(users, dict):
            name = (
                str(users.get("firstName", "")) + " " + str(users.get("lastName", ""))
            ).strip() or "unknown"
        else:
            name = "unknown"
        print(f"✓ Authenticated as: {name}")

        actions = client.list_actions(limit=5)
        items = actions.get("actions", []) if isinstance(actions, dict) else actions
        count = len(items) if isinstance(items, list) else 0
        print(f"✓ Actions accessible: {count} returned (limit 5)")

        return True
    except Exception as e:
        print(f"✗ API check failed: {e}")
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
