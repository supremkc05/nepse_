"""MCP tool definitions for the NEPSE server."""

from typing import Annotated, Literal, Optional

from nepse_mcp.client import NepseAPIClient
from nepse_mcp.utils import NepseAPIError, validate_date_format


def register_tools(mcp) -> None:
    """Register all MCP tools on the given FastMCP instance."""

    @mcp.tool(
        description=(
            "Retrieve current/live trading data for a specific NEPSE-listed stock "
            "or for the entire market. When stock_symbol is omitted or empty, "
            "returns all stocks along with a market-wide summary."
        )
    )
    async def get_live_market_data(
        stock_symbol: Annotated[
            Optional[str],
            "Ticker symbol (e.g. 'NABIL'). Leave empty to fetch all stocks.",
        ] = None,
    ) -> dict:
        """Get current trading data for one stock or the whole market."""
        try:
            async with NepseAPIClient() as client:
                result = await client.get_stock_live(
                    stock_symbol=stock_symbol or ""
                )
            return result.model_dump()
        except NepseAPIError as exc:
            return {"error": str(exc)}

    @mcp.tool(
        description=(
            "Retrieve historical dividend (bonus shares, cash dividends) and "
            "rights issuance records for a NEPSE-listed company. Results are "
            "paginated — use page_no to request additional pages when "
            "has_more_data is True."
        )
    )
    async def get_dividend_history(
        stock_symbol: Annotated[str, "Ticker symbol (e.g. 'NABIL')."],
        fiscal_year_id: Annotated[
            int, "Fiscal year ID filter; 0 means all fiscal years."
        ] = 0,
        limit: Annotated[
            int, "Number of records per page (default 20, max 100)."
        ] = 20,
        page_no: Annotated[int, "Page number (1-indexed)."] = 1,
    ) -> dict:
        """Get dividend and rights history for a stock."""
        try:
            async with NepseAPIClient() as client:
                page = await client.get_dividend_rights(
                    stock_symbol=stock_symbol,
                    fiscal_year_id=fiscal_year_id,
                    page_no=page_no,
                    items_per_page=min(limit, 100),
                )
            return {
                "stock_symbol": stock_symbol,
                "page_no": page.pager.pageNo,
                "has_more_data": page.pager.totalNextPages > 0,
                "total_additional_pages": page.pager.totalNextPages,
                "records": [r.model_dump() for r in page.data],
            }
        except NepseAPIError as exc:
            return {"error": str(exc)}

    @mcp.tool(
        description=(
            "Retrieve daily OHLC (Open, High, Low, Close) price history and "
            "volume data for a NEPSE-listed stock over a specified date range. "
            "Results are paginated — use page_no to fetch additional pages when "
            "has_more_data is True. Dates must be in YYYY-MM-DD format."
        )
    )
    async def get_price_history(
        stock_symbol: Annotated[str, "Ticker symbol (e.g. 'NABIL')."],
        from_date: Annotated[
            str, "Start of date range in YYYY-MM-DD format (e.g. '2026-01-01')."
        ],
        to_date: Annotated[
            str, "End of date range in YYYY-MM-DD format (e.g. '2026-09-03')."
        ],
        limit: Annotated[
            int, "Number of records per page (default 20, max 100)."
        ] = 20,
        page_no: Annotated[int, "Page number (1-indexed)."] = 1,
    ) -> dict:
        """Get daily price history for a stock over a date range."""
        try:
            validate_date_format(from_date)
            validate_date_format(to_date)
        except ValueError as exc:
            return {"error": str(exc)}

        try:
            async with NepseAPIClient() as client:
                page = await client.get_stock_history(
                    stock_symbol=stock_symbol,
                    from_date=from_date,
                    to_date=to_date,
                    page_no=page_no,
                    items_per_page=min(limit, 100),
                )
            return {
                "stock_symbol": stock_symbol,
                "from_date": from_date,
                "to_date": to_date,
                "page_no": page.pager.pageNo,
                "has_more_data": page.pager.totalNextPages > 0,
                "total_additional_pages": page.pager.totalNextPages,
                "records": [r.model_dump() for r in page.data],
            }
        except NepseAPIError as exc:
            return {"error": str(exc)}

    @mcp.tool(
        description=(
            "Retrieve a ranked list of NEPSE stocks by a chosen market indicator. "
            "Supported indicators: 'gainers' (top price gainers), 'turnover' "
            "(highest trading turnover by amount), 'sharestraded' (most shares "
            "traded by volume). Optionally filter by sector_code."
        )
    )
    async def get_top_market_movers(
        indicator: Annotated[
            Literal["gainers", "turnover", "sharestraded"],
            "Ranking metric: 'gainers', 'turnover', or 'sharestraded'.",
        ],
        sector_code: Annotated[
            str,
            "Sector code filter (leave empty for all sectors).",
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
                    sector_code=sector_code,
                    limit=min(limit, 100),
                )
            return {
                "indicator": indicator,
                "sector_code": sector_code or "all",
                "count": len(movers),
                "movers": [m.model_dump() for m in movers],
            }
        except NepseAPIError as exc:
            return {"error": str(exc)}
