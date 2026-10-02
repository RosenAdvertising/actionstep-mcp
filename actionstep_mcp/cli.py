"""Credential-free help for the setup and verification console scripts."""

import sys


def _help(command: str, description: str) -> bool:
    if not any(arg in {"--help", "-h"} for arg in sys.argv[1:]):
        return False
    print(f"Usage: {command} [-h | --help]\n\n{description}\n")
    print("Options:\n  -h, --help  Show this help message and exit.")
    return True


def setup_main() -> None:
    """Show help before loading the interactive setup implementation."""
    if _help(
        "actionstep-mcp-setup",
        "Configure credentials interactively for actionstep-mcp.",
    ):
        return
    from actionstep_mcp.setup.oauth_flow import main

    main()


def verify_main() -> None:
    """Show help before loading configuration or contacting the vendor."""
    if _help(
        "actionstep-mcp-verify", "Verify the configured actionstep-mcp connection."
    ):
        return
    from actionstep_mcp.setup.verify import main

    main()
