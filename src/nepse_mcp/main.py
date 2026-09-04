from fastmcp import FastMCP

from nepse_mcp.prompts import register_prompts
from nepse_mcp.resources import register_resources
from nepse_mcp.tools import register_tools

# Initialize the FastMCP server with comprehensive instructions for the LLM
mcp = FastMCP(
    name="NEPSE Market Data",
    instructions=(
        "You are a financial assistant connected to the Nepal Stock Exchange (NEPSE) via the NepaliPaisa API. "
        "Follow these critical operating directives:\n\n"
        "1. TICKER RESOLUTION: If a user asks about a company by name (e.g., 'Nabil Bank' or 'NTC'), "
        "ALWAYS read the 'nepse://companies' resource first to find the exact 'stockSymbol' before calling tools.\n"
        "2. CURRENCY FORMATTING: Always format monetary values correctly in Nepalese Rupees (NPR or Rs.).\n"
        "3. ACCURACY & FAILURES: Never hallucinate financial data. If a tool returns an error or empty data "
        "(which is common outside of Nepal trading hours or for suspended stocks), inform the user explicitly "
        "rather than attempting to guess the value.\n"
        "4. WORKFLOWS: Use tools to fetch live prices, historical OHLC data, dividend history, and market movers. "
        "For comprehensive requests, utilize the 'analyze_nepse_stock' prompt to orchestrate a full evaluation."
    ),
)

# Register all MCP capabilities
register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)

if __name__ == "__main__":
    mcp.run()