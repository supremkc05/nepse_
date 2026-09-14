import json

from nepse_mcp.client import NepseAPIClient
from nepse_mcp.utils import NepseAPIError

MARKET_GLOSSARY = {
    "currency": "All monetary values are in Nepalese Rupees (NPR / Rs.).",
    "fields": {
        "closingPrice": "Last traded price (LTP) or session close.",
        "previousClosing": "Previous session close used for day change calculations.",
        "dayChange": "Absolute price change versus previous close (NPR).",
        "percentChange": "Percentage change versus previous close.",
        "dayHigh": "Highest traded price in the session.",
        "dayLow": "Lowest traded price in the session.",
        "openingPrice": "First traded price of the session.",
        "volume": "Total number of shares traded.",
        "turnover": "Total traded value in NPR (formerly amount).",
        "noOfTransactions": "Number of executed trades.",
        "sma5": "Simple moving average of the last 5 closing prices.",
        "sma10": "Simple moving average of the last 10 closing prices.",
        "sma20": "Simple moving average of the last 20 closing prices.",
        "maxDrawdown": "Largest peak-to-trough percentage decline in the window.",
        "volatility": "Sample standard deviation of daily percent changes.",
        "volumeTrend": "Whether recent volume is increasing, decreasing, or stable.",
        "trend": "Direction label derived from first vs last close in the window.",
        "sevenDayReturn": "Percent return over the last 7 trading sessions when available.",
        "thirtyDayReturn": "Percent return over the last 30 trading sessions when available.",
    },
    "indicators": {
        "gainers": "Rank stocks by highest percentChange.",
        "turnover": "Rank stocks by highest traded value (NPR).",
        "sharestraded": "Rank stocks by highest share volume.",
    },
    "sectors": {
        "Commercial Banks": "Commercial banking companies.",
        "Development Banks": "Development banking companies.",
        "Finance": "Finance companies.",
        "Microfinance": "Microfinance institutions.",
        "Life Insurance": "Life insurance companies.",
        "Non Life Insurance": "Non-life insurance companies.",
        "Hydropower": "Hydropower and energy companies.",
        "Manufacturing And Processing": "Manufacturing and processing companies.",
        "Hotels And Tourism": "Hotels and tourism companies.",
        "Trading": "Trading companies.",
        "Others": "Other listed securities / sectors.",
        "note": (
            "Sector filtering via sector_code depends on upstream NepaliPaisa codes. "
            "Prefer company.sectorName from search_companies when identifying sectors."
        ),
    },
    "response_flags": {
        "data_complete": "True when all expected fields for the request are present.",
        "warning": "Human-readable note when metrics are partial or pagination remains.",
        "source_gap_detected": "True when upstream data is too short or incomplete for full analytics.",
    },
}

ANALYSIS_RULES = {
    "momentum": [
        "Prefer server-computed fields (percentReturn, sevenDayReturn, thirtyDayReturn, trend) over recalculating from raw rows.",
        "Treat uptrend/downtrend as descriptive labels for the requested window, not investment advice.",
        "If volumeTrend is increasing with an uptrend, volume confirms strength; if volume falls while price rises, note divergence.",
        "When SMA values are present, price above SMA5/SMA10/SMA20 is short-term constructive; below is weak — only for the given window.",
        "If data_complete is false or source_gap_detected is true, state uncertainty explicitly and do not invent missing SMA/returns.",
    ],
    "dividends": [
        "Bonus and cash are percentages, not NPR amounts per share.",
        "totalDividend is bonus + cash as reported; rights issues are separate via rightShare.",
        "Skip years with missing or zero payouts when judging consistency; gaps may be fiscal-year coverage issues, not policy changes.",
        "Do not project future dividends from past payouts.",
    ],
    "caveats": [
        "NEPSE data comes from an unofficial NepaliPaisa API and may be delayed, incomplete, or unavailable outside trading hours.",
        "Never hallucinate prices, volumes, dividends, or rankings. If a tool errors or returns empty data, say so.",
        "Prefer search_companies for ticker lookup; use nepse://companies only when a full directory is required.",
        "Prefer get_stock_snapshot and get_price_history_summary before requesting full get_price_history rows.",
        "Call get_market_glossary and get_analysis_rules before explaining metrics when resources are unavailable.",
        "Always format money as NPR/Rs. and mention when metrics are based on partial history.",
    ],
}


def register_resources(mcp) -> None:
    """Register all MCP resources on the given FastMCP instance."""

    @mcp.resource(
        "nepse://companies",
        name="nepse_companies",
        description=(
            "Full NEPSE company directory (names, tickers, sectors). "
            "Prefer search_companies for ticker lookup; read this only when you need the full list."
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
                "Failed to fetch the NEPSE company directory. "
                f"Underlying API error: {exc}"
            ) from exc

    @mcp.resource(
        "nepse://market-glossary",
        name="nepse_market_glossary",
        description=(
            "Definitions for NEPSE field names, market indicators, sectors, and response flags. "
            "Read this before interpreting tool output or explaining metrics to the user."
        ),
        mime_type="application/json",
    )
    async def get_market_glossary() -> str:
        """Return static market field and indicator definitions."""
        return json.dumps(MARKET_GLOSSARY)

    @mcp.resource(
        "nepse://analysis-rules",
        name="nepse_analysis_rules",
        description=(
            "Interpretation rules for momentum, dividends, and common caveats. "
            "Follow these to avoid hallucinated finance explanations."
        ),
        mime_type="application/json",
    )
    async def get_analysis_rules() -> str:
        """Return static analysis guidance for LLM clients."""
        return json.dumps(ANALYSIS_RULES)
