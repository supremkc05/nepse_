import datetime
from fastmcp.prompts.base import Message

def register_prompts(mcp) -> None:
    """Register all MCP prompts on the given FastMCP instance."""

    @mcp.prompt(
        name="analyze_nepse_stock",
        description=(
            "Instructs the assistant to perform a comprehensive fundamental and "
            "technical analysis of a NEPSE-listed stock by orchestrating tools "
            "for live price, 30-day history, and dividend data."
        ),
    )
    def analyze_nepse_stock(ticker: str) -> list[Message]:
        """Return a structured analysis prompt for the given NEPSE ticker."""
        
        # Calculate dates explicitly so the LLM doesn't have to guess relative time
        today = datetime.date.today()
        thirty_days_ago = today - datetime.timedelta(days=30)
        
        # Ensure the ticker is standardized
        clean_ticker = ticker.strip().upper()

        return [
            Message(
                role="user",
                content=(
                    f"Act as a financial analyst specializing in the Nepal Stock Exchange (NEPSE). "
                    f"Please perform a comprehensive analysis for the ticker '{clean_ticker}'.\n\n"
                    f"Today's date is {today.isoformat()}. Follow these steps strictly in order:\n\n"
                    f"### 1. Fetch Live Market Data\n"
                    f"Call `get_live_market_data` with stock_symbol='{clean_ticker}'. Note the current price, "
                    f"trading volume, intraday high/low, and percentage change.\n\n"
                    f"### 2. Fetch Recent Price History\n"
                    f"Call `get_price_history` with stock_symbol='{clean_ticker}', "
                    f"from_date='{thirty_days_ago.isoformat()}', and to_date='{today.isoformat()}'. "
                    f"If `has_more_data` is True, evaluate if an additional page is necessary to determine the trend.\n\n"
                    f"### 3. Fetch Dividend History\n"
                    f"Call `get_dividend_history` with stock_symbol='{clean_ticker}' to evaluate "
                    f"long-term value creation (bonus shares and cash dividends).\n\n"
                    f"### 4. Synthesize and Report\n"
                    f"Compile your findings into a professional markdown report with the following structure:\n"
                    f"- **Live Snapshot:** Current price, daily performance vs. previous close, and volume context.\n"
                    f"- **30-Day Trend Analysis:** Volatility, key support/resistance levels, and overall price direction.\n"
                    f"- **Dividend Track Record:** Consistency of payouts (use a Markdown table summarizing the recent years).\n"
                    f"- **Analyst Conclusion:** State clearly whether the stock exhibits bullish, bearish, or sideways momentum based on the data.\n\n"
                    f"*Guardrail: If any tool returns empty data or an error (common outside trading hours or for newly listed stocks), state this explicitly rather than estimating values.*"
                ),
            )
        ]