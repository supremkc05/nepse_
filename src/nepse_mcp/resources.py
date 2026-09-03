"""MCP resource definitions for the NEPSE server."""

from nepse_mcp.client import NepseAPIClient
from nepse_mcp.utils import NepseAPIError


def register_resources(mcp) -> None:
    """Register all MCP resources on the given FastMCP instance."""

    @mcp.resource(
        "nepse://companies",
        name="nepse_companies",
        description=(
            "Complete list of all companies and securities listed on the Nepal "
            "Stock Exchange (NEPSE), including their ticker symbols and sector "
            "classifications. Use this to map company names to the stockSymbol "
            "format required by other tools."
        ),
        mime_type="application/json",
    )
    async def get_companies() -> list[dict]:
        """Return the full NEPSE company listing."""
        try:
            async with NepseAPIClient() as client:
                companies = await client.get_companies()
            return [c.model_dump() for c in companies]
        except NepseAPIError as exc:
            raise RuntimeError(str(exc)) from exc
