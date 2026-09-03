"""FastMCP server instance and entry point for the NEPSE MCP server."""

from fastmcp import FastMCP

from nepse_mcp.prompts import register_prompts
from nepse_mcp.resources import register_resources
from nepse_mcp.tools import register_tools

mcp = FastMCP(
    "NEPSE Market Data",
    instructions=(
        "This server provides Nepal Stock Exchange (NEPSE) market data from the "
        "NepaliPaisa API. Use the 'nepse://companies' resource to look up ticker "
        "symbols, then use the tools to fetch live prices, price history, "
        "dividends, and market movers. The 'analyze_nepse_stock' prompt "
        "orchestrates a full stock analysis."
    ),
)

register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)
