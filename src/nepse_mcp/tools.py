from typing import Annotated, Literal, Optional

from nepse_mcp.client import NepseAPIClient
from nepse_mcp.resources import ANALYSIS_RULES, MARKET_GLOSSARY
from nepse_mcp.utils import (
    NepseAPIError,
    build_tool_response,
    summarize_history_gaps,
    to_compact_dividend_record,
    to_compact_live_result,
    to_compact_live_stock,
    to_compact_price_history_record,
    validate_date_format,
)


def register_tools(mcp) -> None:
    """Register all MCP tools on the given FastMCP instance."""

    @mcp.tool(
        name="get_live_market_data",
        description=(
            "Retrieve current/live trading data (price, volume, high/low, % change) "
            "for a specific NEPSE-listed stock or the entire market. "
            "If analyzing a specific company, always provide the stock_symbol. "
            "Leave stock_symbol empty ONLY when a full market overview is explicitly requested."
        ),
    )
    async def get_live_market_data(
        stock_symbol: Annotated[
            Optional[str],
            "Ticker symbol (e.g., 'NABIL'). Leave empty for all stocks.",
        ] = None,
    ) -> dict:
        """Get current trading data for one stock or the whole market."""
        try:
            clean_symbol = stock_symbol.strip().upper() if stock_symbol else ""
            async with NepseAPIClient() as client:
                result = await client.get_stock_live(stock_symbol=clean_symbol)
            compact = to_compact_live_result(result)
            return build_tool_response(data=compact.model_dump())
        except NepseAPIError as exc:
            return build_tool_response(status="error", error_message=str(exc))

    @mcp.tool(
        name="search_companies",
        description=(
            "Search the NEPSE company directory by ticker symbol or company name. "
            "Prefer this over reading the full company resource when you only need a few matches."
        ),
    )
    async def search_companies(
        query: Annotated[str, "Partial or exact company name / ticker, e.g. 'NABIL' or 'Nabil'."],
        limit: Annotated[int, "Maximum matches to return, capped at 20."] = 5,
    ) -> dict:
        """Search the company directory with compact match results."""
        try:
            async with NepseAPIClient() as client:
                matches = await client.search_companies(query=query, limit=min(limit, 20))
            return build_tool_response(
                query=query,
                count=len(matches),
                matches=[match.model_dump() for match in matches],
            )
        except NepseAPIError as exc:
            return build_tool_response(status="error", error_message=str(exc))

    @mcp.tool(
        name="get_stock_snapshot",
        description=(
            "Return a compact live snapshot for a single NEPSE stock. "
            "Use this for stock overviews instead of requesting broader live market payloads."
        ),
    )
    async def get_stock_snapshot(
        stock_symbol: Annotated[str, "Ticker symbol (e.g., 'NABIL')."],
    ) -> dict:
        """Get a compact live snapshot for one stock."""
        try:
            async with NepseAPIClient() as client:
                snapshot = await client.get_stock_snapshot(
                    stock_symbol=stock_symbol.strip().upper()
                )
            return build_tool_response(data=snapshot.model_dump())
        except NepseAPIError as exc:
            return build_tool_response(status="error", error_message=str(exc))

    @mcp.tool(
        name="get_dividend_history",
        description=(
            "Retrieve historical corporate actions, specifically bonus shares, "
            "cash dividends, and rights issuances for a NEPSE-listed company. "
            "Use this to evaluate a company's historical yield and payout consistency. "
            "Check 'has_more_data' in the response; if True, increment 'page_no' to fetch more."
        ),
    )
    async def get_dividend_history(
        stock_symbol: Annotated[str, "Ticker symbol (e.g., 'NABIL')."],
        fiscal_year_id: Annotated[
            int, "Fiscal year ID filter. Default is 0 (returns all fiscal years)."
        ] = 0,
        limit: Annotated[
            int, "Records per page. Max 100. Default to 100 to minimize pagination loops."
        ] = 100,
        page_no: Annotated[int, "Page number to fetch (1-indexed)."] = 1,
    ) -> dict:
        """Get dividend and rights history for a stock."""
        try:
            async with NepseAPIClient() as client:
                page = await client.get_dividend_rights(
                    stock_symbol=stock_symbol.strip().upper(),
                    fiscal_year_id=fiscal_year_id,
                    page_no=page_no,
                    items_per_page=min(limit, 100),
                )
            has_more = page.pager.totalNextPages > 0
            return build_tool_response(
                data_complete=not has_more,
                warning=(
                    "Additional pages are available; increase page_no to fetch more records."
                    if has_more
                    else None
                ),
                source_gap_detected=has_more,
                stock_symbol=stock_symbol.strip().upper(),
                page_no=page.pager.pageNo,
                has_more_data=has_more,
                total_additional_pages=page.pager.totalNextPages,
                records=[to_compact_dividend_record(r).model_dump() for r in page.data],
            )
        except NepseAPIError as exc:
            return build_tool_response(status="error", error_message=str(exc))

    @mcp.tool(
        name="get_price_history",
        description=(
            "Retrieve daily OHLC (Open, High, Low, Close) price history and volume "
            "data for a NEPSE-listed stock over a specified date range. "
            "Crucial for technical analysis and identifying price trends. "
            "Dates MUST be in YYYY-MM-DD format."
        ),
    )
    async def get_price_history(
        stock_symbol: Annotated[str, "Ticker symbol (e.g., 'NICA')."],
        from_date: Annotated[
            str, "Start date in YYYY-MM-DD format (e.g., '2026-01-01')."
        ],
        to_date: Annotated[
            str, "End date in YYYY-MM-DD format (e.g., '2026-09-03')."
        ],
        limit: Annotated[
            int, "Records per page. Max 100. Default to 100 to get more data per call."
        ] = 100,
        page_no: Annotated[int, "Page number (1-indexed)."] = 1,
    ) -> dict:
        """Get daily price history for a stock over a date range."""
        try:
            validate_date_format(from_date)
            validate_date_format(to_date)
        except ValueError as exc:
            return build_tool_response(
                status="error",
                error_message=f"Invalid date format: {exc}",
            )

        try:
            async with NepseAPIClient() as client:
                page = await client.get_stock_history(
                    stock_symbol=stock_symbol.strip().upper(),
                    from_date=from_date,
                    to_date=to_date,
                    page_no=page_no,
                    items_per_page=min(limit, 100),
                )
            has_more = page.pager.totalNextPages > 0
            return build_tool_response(
                data_complete=not has_more,
                warning=(
                    "Additional pages are available; increase page_no to fetch more records."
                    if has_more
                    else None
                ),
                source_gap_detected=has_more,
                stock_symbol=stock_symbol.strip().upper(),
                from_date=from_date,
                to_date=to_date,
                page_no=page.pager.pageNo,
                has_more_data=has_more,
                total_additional_pages=page.pager.totalNextPages,
                records=[
                    to_compact_price_history_record(r).model_dump() for r in page.data
                ],
            )
        except NepseAPIError as exc:
            return build_tool_response(status="error", error_message=str(exc))

    @mcp.tool(
        name="get_price_history_summary",
        description=(
            "Return compact, derived price-history metrics for a single stock over a date range. "
            "Prefer this over raw history when you want trend and performance analysis."
        ),
    )
    async def get_price_history_summary(
        stock_symbol: Annotated[str, "Ticker symbol (e.g., 'NABIL')."],
        from_date: Annotated[str, "Start date in YYYY-MM-DD format."],
        to_date: Annotated[str, "End date in YYYY-MM-DD format."],
    ) -> dict:
        """Get summary metrics for a stock's price history."""
        try:
            validate_date_format(from_date)
            validate_date_format(to_date)
        except ValueError as exc:
            return build_tool_response(
                status="error",
                error_message=f"Invalid date format: {exc}",
            )

        try:
            async with NepseAPIClient() as client:
                summary = await client.get_price_history_summary(
                    stock_symbol=stock_symbol.strip().upper(),
                    from_date=from_date,
                    to_date=to_date,
                )
            data_complete, source_gap_detected, warning = summarize_history_gaps(summary)
            return build_tool_response(
                data=summary.model_dump(),
                data_complete=data_complete,
                warning=warning,
                source_gap_detected=source_gap_detected,
            )
        except NepseAPIError as exc:
            return build_tool_response(status="error", error_message=str(exc))

    @mcp.tool(
        name="get_top_market_movers",
        description=(
            "Retrieve a ranked list of NEPSE stocks by a chosen market indicator. "
            "Use this to find top performing stocks, most actively traded shares, "
            "or highest turnover. Can optionally filter by specific NEPSE sector codes."
        ),
    )
    async def get_top_market_movers(
        indicator: Annotated[
            Literal["gainers", "turnover", "sharestraded"],
            "Ranking metric: 'gainers' (top % change), 'turnover' (total Rs amount), or 'sharestraded' (total volume).",
        ],
        sector_code: Annotated[
            str,
            "Optional sector code filter. Leave empty string for all sectors.",
        ] = "",
        limit: Annotated[
            int,
            "Maximum number of results to return (default 20, max 100).",
        ] = 20,
    ) -> dict:
        """Get top market movers ranked by the chosen indicator."""
        try:
            async with NepseAPIClient() as client:
                movers = await client.get_top_market_movers(
                    indicator=indicator,
                    sector_code=sector_code.strip(),
                    limit=min(limit, 100),
                )
            return build_tool_response(
                indicator=indicator,
                sector_code=sector_code or "all",
                count=len(movers),
                movers=[to_compact_live_stock(m).model_dump() for m in movers],
            )
        except NepseAPIError as exc:
            return build_tool_response(status="error", error_message=str(exc))

    @mcp.tool(
        name="compare_stocks",
        description=(
            "Compare multiple NEPSE stocks by a fixed metric and return ranked compact results. "
            "Use this instead of manually comparing raw payloads."
        ),
    )
    async def compare_stocks(
        stock_symbols: Annotated[list[str], "Ticker symbols to compare, e.g. ['NABIL', 'ADBL']."],
        metric: Annotated[
            Literal["closing_price", "percent_change", "volume", "turnover", "30d_return"],
            "Comparison metric: closing_price, percent_change, volume, turnover, or 30d_return.",
        ],
    ) -> dict:
        """Compare stocks by a compact fixed metric."""
        try:
            unique_symbols = list(
                dict.fromkeys(
                    symbol.strip().upper() for symbol in stock_symbols if symbol.strip()
                )
            )
            async with NepseAPIClient() as client:
                comparison = await client.compare_stocks(
                    stock_symbols=unique_symbols,
                    metric=metric,
                )
            incomplete = len(comparison.rankings) < len(unique_symbols)
            warning = None
            if incomplete:
                warning = (
                    "Some requested symbols could not be ranked because live or history "
                    "data was unavailable."
                )
            return build_tool_response(
                data=comparison.model_dump(),
                data_complete=not incomplete,
                warning=warning,
                source_gap_detected=incomplete,
            )
        except NepseAPIError as exc:
            return build_tool_response(status="error", error_message=str(exc))

    @mcp.tool(
        name="get_market_glossary",
        description=(
            "Return definitions for NEPSE field names, indicators, sectors, and response flags. "
            "Call this before explaining metrics like turnover, SMA20, or source_gap_detected. "
            "Prefer this tool over nepse://market-glossary when the client cannot read resources."
        ),
    )
    async def get_market_glossary() -> dict:
        """Return the static market glossary as a tool payload."""
        return build_tool_response(data=MARKET_GLOSSARY)

    @mcp.tool(
        name="get_analysis_rules",
        description=(
            "Return interpretation rules for momentum, dividends, and common caveats. "
            "Call this before giving analysis explanations so answers stay grounded. "
            "Prefer this tool over nepse://analysis-rules when the client cannot read resources."
        ),
    )
    async def get_analysis_rules() -> dict:
        """Return the static analysis rules as a tool payload."""
        return build_tool_response(data=ANALYSIS_RULES)
