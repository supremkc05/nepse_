"""MCP prompt definitions for the NEPSE server."""

from fastmcp.prompts.base import Message


def register_prompts(mcp) -> None:
    """Register all MCP prompts on the given FastMCP instance."""

    @mcp.prompt(
        name="analyze_nepse_stock",
        description=(
            "Guides the assistant to perform a comprehensive fundamental and "
            "technical analysis of a NEPSE-listed stock by orchestrating multiple "
            "tool calls: live price, 30-day price history, and dividend history."
        ),
    )
    def analyze_nepse_stock(
        ticker: str,
    ) -> list[Message]:
        """Return a structured analysis prompt for the given NEPSE ticker."""
        return [
            Message(
                role="user",
                content=(
                    f"Please perform a comprehensive analysis of the NEPSE-listed "
                    f"stock with ticker '{ticker}'. Follow these steps in order:\n\n"
                    f"1. **Live market data** — Call `get_live_market_data` with "
                    f"stock_symbol='{ticker}' to get the current price, volume, "
                    f"and intraday price range.\n\n"
                    f"2. **Recent price history (last 30 days)** — Call "
                    f"`get_price_history` with stock_symbol='{ticker}', setting "
                    f"from_date to 30 days ago and to_date to today. If "
                    f"has_more_data is True, decide whether additional pages are "
                    f"needed for the analysis.\n\n"
                    f"3. **Dividend history** — Call `get_dividend_history` with "
                    f"stock_symbol='{ticker}' to retrieve the company's bonus "
                    f"share and cash dividend track record.\n\n"
                    f"4. **Synthesis** — Using the data gathered above, provide:\n"
                    f"   - Current price and day's performance vs previous close\n"
                    f"   - 30-day price trend (direction, volatility, notable "
                    f"     highs/lows)\n"
                    f"   - Dividend yield history and consistency\n"
                    f"   - Overall assessment: is this stock showing bullish, "
                    f"     bearish, or sideways momentum?\n\n"
                    f"Present the findings clearly, using tables where helpful."
                ),
            )
        ]
