import json
from nepse_mcp.client import NepseAPIClient
from nepse_mcp.utils import NepseAPIError


def register_resources(mcp) -> None:
    """Register all MCP resources on the given FastMCP instance."""

    @mcp.resource(
        "nepse://companies",
        name="nepse_companies",
        description=(
            "A comprehensive directory of all companies and securities listed on "
            "the Nepal Stock Exchange (NEPSE). Includes company names, ticker "
            "symbols (stockSymbol), and sector information. "
            "CRITICAL: Always read this resource to resolve a company's name "
            "(e.g., 'Nabil Bank') into its exact 'stockSymbol' (e.g., 'NABIL') "
            "BEFORE calling any pricing or dividend tools."
        ),
        mime_type="application/json",
    )
    async def get_companies() -> str:
        """Return the full NEPSE company listing as a JSON string."""
        try:
            async with NepseAPIClient() as client:
                companies = await client.get_companies()
            
            return json.dumps([c.model_dump() for c in companies])
            
        except NepseAPIError as exc:
            raise RuntimeError(
                f"Failed to fetch the NEPSE company directory. "
                f"Underlying API error: {exc}"
            ) from exc