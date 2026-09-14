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
        "1. TICKER RESOLUTION: Prefer search_companies for name/ticker lookup. "
        "Read nepse://companies only when a full directory is required.\n"
        "2. TOOL ORDER: For stock questions use search_companies -> get_stock_snapshot -> "
        "get_price_history_summary. Call get_price_history only when raw OHLC rows are needed.\n"
        "3. INTERPRETATION: Call get_market_glossary for field meanings and "
        "get_analysis_rules for momentum/dividend caveats before explaining results "
        "(Claude Desktop may not support reading nepse:// resources).\n"
        "4. COMPLETENESS: Honor data_complete, warning, and source_gap_detected. "
        "If data is partial, say so; never invent missing SMA, returns, or prices.\n"
        "5. CURRENCY: Always format monetary values in Nepalese Rupees (NPR or Rs.).\n"
        "6. ACCURACY: Never hallucinate financial data. If a tool errors or returns empty data "
        "(common outside trading hours), tell the user explicitly.\n"
        "7. WORKFLOWS: For comprehensive requests, use the analyze_nepse_stock prompt."
    ),
)

# Register all MCP capabilities
register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)

if __name__ == "__main__":
    mcp.run()
