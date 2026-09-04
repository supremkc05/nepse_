from typing import Annotated, Literal, Optional

from nepse_mcp.client import NepseAPIClient
from nepse_mcp.utils import NepseAPIError, validate_date_format


def register_tools(mcp) -> None:
    """Register all MCP tools on the given FastMCP instance."""

    @mcp.tool(
        name="get_live_market_data",
        description=(
            "Retrieve current/live trading data (price, volume, high/low, % change) "
            "for a specific NEPSE-listed stock or the entire market. "
            "If analyzing a specific company, always provide the stock_symbol. "
            "Leave stock_symbol empty ONLY when a full market overview is explicitly requested."
        )
    )
    async def get_live_market_data(
        stock_symbol: Annotated[
            Optional[str],
            "Ticker symbol (e.g., 'NABIL'). Leave empty for all stocks.",
        ] = None,
    ) -> dict:
        """Get current trading data for one stock or the whole market."""
        try:
            # Clean ticker if provided
            clean_symbol = stock_symbol.strip().upper() if stock_symbol else ""
            async with NepseAPIClient() as client:
                result = await client.get_stock_live(stock_symbol=clean_symbol)
            return {"status": "success", "data": result.model_dump()}
        except NepseAPIError as exc:
            return {"status": "error", "error_message": str(exc)}

    @mcp.tool(
        name="get_dividend_history",
        description=(
            "Retrieve historical corporate actions, specifically bonus shares, "
            "cash dividends, and rights issuances for a NEPSE-listed company. "
            "Use this to evaluate a company's historical yield and payout consistency. "
            "Check 'has_more_data' in the response; if True, increment 'page_no' to fetch more."
        )
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
            return {
                "status": "success",
                "stock_symbol": stock_symbol.upper(),
                "page_no": page.pager.pageNo,
                "has_more_data": page.pager.totalNextPages > 0,
                "total_additional_pages": page.pager.totalNextPages,
                "records": [r.model_dump() for r in page.data],
            }
        except NepseAPIError as exc:
            return {"status": "error", "error_message": str(exc)}

    @mcp.tool(
        name="get_price_history",
        description=(
            "Retrieve daily OHLC (Open, High, Low, Close) price history and volume "
            "data for a NEPSE-listed stock over a specified date range. "
            "Crucial for technical analysis and identifying price trends. "
            "Dates MUST be in YYYY-MM-DD format."
        )
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
            return {"status": "error", "error_message": f"Invalid date format: {exc}"}

        try:
            async with NepseAPIClient() as client:
                page = await client.get_stock_history(
                    stock_symbol=stock_symbol.strip().upper(),
                    from_date=from_date,
                    to_date=to_date,
                    page_no=page_no,
                    items_per_page=min(limit, 100),
                )
            return {
                "status": "success",
                "stock_symbol": stock_symbol.upper(),
                "from_date": from_date,
                "to_date": to_date,
                "page_no": page.pager.pageNo,
                "has_more_data": page.pager.totalNextPages > 0,
                "total_additional_pages": page.pager.totalNextPages,
                "records": [r.model_dump() for r in page.data],
            }
        except NepseAPIError as exc:
            return {"status": "error", "error_message": str(exc)}

    @mcp.tool(
        name="get_top_market_movers",
        description=(
            "Retrieve a ranked list of NEPSE stocks by a chosen market indicator. "
            "Use this to find top performing stocks, most actively traded shares, "
            "or highest turnover. Can optionally filter by specific NEPSE sector codes."
        )
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
            return {
                "status": "success",
                "indicator": indicator,
                "sector_code": sector_code or "all",
                "count": len(movers),
                "movers": [m.model_dump() for m in movers],
            }
        except NepseAPIError as exc:
            return {"status": "error", "error_message": str(exc)}