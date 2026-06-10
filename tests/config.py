from pathlib import Path

from mcp_test_kit.config import ResilienceConfig, SpecCheckConfig, ToolkitConfig
from actionstep_mcp.server import mcp

_TESTS_DIR = Path(__file__).parent

TOOLKIT = ToolkitConfig(
    mcp_server=mcp,
    spec_check=SpecCheckConfig(
        endpoints_path=_TESTS_DIR.parent / "endpoints.yaml",
        openapi_path=_TESTS_DIR.parent
        / "endpoints.yaml",  # dummy — contract tier skipped
    ),
    source_path=_TESTS_DIR.parent / "actionstep_mcp",
    module_path="actionstep_mcp",
    server_path=_TESTS_DIR.parent / "actionstep_mcp" / "server.py",
    resilience=ResilienceConfig(tools_to_timeout_test=["get_current_user"]),
    skip_tiers={
        "contract": "no published OpenAPI spec for Actionstep API (Postman collection only)",
        "smoke": "requires live sandbox credentials",
    },
)
