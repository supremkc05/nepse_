"""NEPSE MCP server package."""

from nepse_mcp.main import mcp


def main() -> None:
    """Entry point for the nepse-mcp CLI command."""
    mcp.run(transport="stdio", show_banner=False)
