"""Async HTTP client for the NepaliPaisa NEPSE API."""

import time
from typing import Any

import httpx

from nepse_mcp.config import settings
from nepse_mcp.schemas import (
    Company,
    DividendRecord,
    IndicatorType,
    LiveMarketResult,
    PaginatedData,
    Pager,
    PriceHistoryRecord,
    TopMoverItem,
)
from nepse_mcp.utils import NepseAPIError


class NepseAPIClient:
    """Async client that wraps all NepaliPaisa API endpoints.

    Usage (as async context manager):
        async with NepseAPIClient() as client:
            companies = await client.get_companies()
    """

    def __init__(self) -> None:
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "NepseAPIClient":
        self._http = httpx.AsyncClient(
            base_url=settings.nepalipaisa_base_url,
            timeout=settings.http_timeout,
        )
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    # Private helpers

    @property
    def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            raise RuntimeError(
                "NepseAPIClient is not open. Use it as an async context manager."
            )
        return self._http

    @staticmethod
    def _cache_bust() -> int:
        """Return the current epoch time in milliseconds for cache-busting."""
        return int(time.time() * 1000)

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Execute a GET request and validate the response envelope.

        Returns:
            The `result` field from the response JSON.

        Raises:
            NepseAPIError: On HTTP errors, timeouts, or non-200 statusCode in the body.
        """
        if params is None:
            params = {}
        params["_"] = self._cache_bust()

        try:
            response = await self._client.get(path, params=params)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise NepseAPIError(f"Request timed out: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise NepseAPIError(
                f"HTTP {exc.response.status_code} error from {path}"
            ) from exc
        except httpx.RequestError as exc:
            raise NepseAPIError(f"Network error: {exc}") from exc

        try:
            body = response.json()
        except Exception as exc:
            raise NepseAPIError(f"Failed to parse JSON response: {exc}") from exc

        status_code = body.get("statusCode")
        if status_code != 200:
            message = body.get("message", "Unknown error")
            raise NepseAPIError(
                f"API returned statusCode={status_code}: {message}"
            )

        return body.get("result")

    # Public endpoint methods

    async def get_companies(self) -> list[Company]:
        """GET /GetCompanies — full list of NEPSE-listed companies."""
        result = await self._get("/GetCompanies")
        return [Company.model_validate(item) for item in result]

    async def get_stock_live(
        self, stock_symbol: str = ""
    ) -> LiveMarketResult:
        """GET /GetStockLive — live trading data for one or all stocks."""
        result = await self._get(
            "/GetStockLive", params={"stockSymbol": stock_symbol}
        )
        return LiveMarketResult.model_validate(result)

    async def get_dividend_rights(
        self,
        stock_symbol: str,
        fiscal_year_id: int = 0,
        page_no: int = 1,
        items_per_page: int = 20,
    ) -> PaginatedData[DividendRecord]:
        """GET /GetDividendRights — dividend and rights history for a stock."""
        result = await self._get(
            "/GetDividendRights",
            params={
                "stockSymbol": stock_symbol,
                "fiscalYearId": fiscal_year_id,
                "pageNo": page_no,
                "itemsPerPage": items_per_page,
                "pagePerDisplay": 5,
            },
        )
        records = [DividendRecord.model_validate(item) for item in result["data"]]
        pager = Pager.model_validate(result["pager"])
        return PaginatedData[DividendRecord](data=records, pager=pager)

    async def get_stock_history(
        self,
        stock_symbol: str,
        from_date: str,
        to_date: str,
        page_no: int = 1,
        items_per_page: int = 20,
    ) -> PaginatedData[PriceHistoryRecord]:
        """GET /GetStockHistory — daily OHLC price history for a stock."""
        result = await self._get(
            "/GetStockHistory",
            params={
                "stockSymbol": stock_symbol,
                "fromDate": from_date,
                "toDate": to_date,
                "pageNo": page_no,
                "itemsPerPage": items_per_page,
                "pagePerDisplay": 5,
            },
        )
        records = [
            PriceHistoryRecord.model_validate(item) for item in result["data"]
        ]
        pager = Pager.model_validate(result["pager"])
        return PaginatedData[PriceHistoryRecord](data=records, pager=pager)

    async def get_top_market_movers(
        self,
        indicator: IndicatorType,
        sector_code: str = "",
        limit: int = 20,
    ) -> list[TopMoverItem]:
        """GET /GetTopMarketMovers — ranked stocks by the chosen indicator."""
        result = await self._get(
            "/GetTopMarketMovers",
            params={
                "indicator": indicator,
                "sectorCode": sector_code,
                "limit": limit,
            },
        )
        return [TopMoverItem.model_validate(item) for item in result]
