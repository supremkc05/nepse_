import time
from typing import Any, Optional

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

    def __init__(self, client: Optional[httpx.AsyncClient] = None) -> None:
        self._http: httpx.AsyncClient | None = client
        self._external_client: bool = client is not None

    async def __aenter__(self) -> "NepseAPIClient":
        if self._http is None:
            # Set explicit User-Agent and headers to avoid being blocked or rate-limited by API anti-scraping
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json",
            }
            self._http = httpx.AsyncClient(
                base_url=str(settings.nepalipaisa_base_url).rstrip("/"),
                timeout=settings.nepse_http_timeout,
                headers=headers,
                follow_redirects=True,
            )
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._http is not None and not self._external_client:
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
        
        if not path.startswith("/"):
            path = f"/{path}"

        params["_"] = self._cache_bust()

        try:
            response = await self._client.get(path, params=params)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise NepseAPIError(
                f"Request to {path} timed out after {settings.nepse_http_timeout}s."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise NepseAPIError(
                f"HTTP {exc.response.status_code} error from {path}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            raise NepseAPIError(f"Network error connecting to NEPSE API: {exc}") from exc

        try:
            body = response.json()
        except Exception as exc:
            raise NepseAPIError(f"Failed to parse JSON response from {path}: {exc}") from exc

        if not isinstance(body, dict):
            raise NepseAPIError(f"Invalid API response format from {path}: expected JSON object.")

        status_code = body.get("statusCode")
        if status_code is not None and status_code != 200:
            message = body.get("message", "Unknown API error")
            raise NepseAPIError(
                f"API returned statusCode={status_code}: {message}",
                status_code=status_code if isinstance(status_code, int) else None,
            )

        return body.get("result")

    # Public endpoint methods

    async def get_companies(self) -> list[Company]:
        """GET /GetCompanies — full list of NEPSE-listed companies."""
        result = await self._get("/GetCompanies")
        if not isinstance(result, list):
            return []
        return [Company.model_validate(item) for item in result]

    async def get_stock_live(self, stock_symbol: str = "") -> LiveMarketResult:
        """GET /GetStockLive — live trading data for one or all stocks."""
        clean_symbol = stock_symbol.strip().upper() if stock_symbol else ""
        result = await self._get(
            "/GetStockLive", params={"stockSymbol": clean_symbol}
        )
        if not result or not isinstance(result, dict):
            return LiveMarketResult(stocks=[])
        return LiveMarketResult.model_validate(result)

    async def get_dividend_rights(
        self,
        stock_symbol: str,
        fiscal_year_id: int = 0,
        page_no: int = 1,
        items_per_page: int = 20,
    ) -> PaginatedData[DividendRecord]:
        """GET /GetDividendRights — dividend and rights history for a stock."""
        clean_symbol = stock_symbol.strip().upper()
        result = await self._get(
            "/GetDividendRights",
            params={
                "stockSymbol": clean_symbol,
                "fiscalYearId": fiscal_year_id,
                "pageNo": page_no,
                "itemsPerPage": min(items_per_page, 100),
                "pagePerDisplay": 5,
            },
        )

        if not result or not isinstance(result, dict):
            return PaginatedData[DividendRecord](
                data=[],
                pager=Pager(pageNo=page_no, itemsPerPage=items_per_page, pagePerDisplay=5, totalNextPages=0),
            )

        raw_records = result.get("data") or []
        raw_pager = result.get("pager") or {
            "pageNo": page_no,
            "itemsPerPage": items_per_page,
            "pagePerDisplay": 5,
            "totalNextPages": 0,
        }

        records = [DividendRecord.model_validate(item) for item in raw_records]
        pager = Pager.model_validate(raw_pager)
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
        clean_symbol = stock_symbol.strip().upper()
        result = await self._get(
            "/GetStockHistory",
            params={
                "stockSymbol": clean_symbol,
                "fromDate": from_date,
                "toDate": to_date,
                "pageNo": page_no,
                "itemsPerPage": min(items_per_page, 100),
                "pagePerDisplay": 5,
            },
        )

        if not result or not isinstance(result, dict):
            return PaginatedData[PriceHistoryRecord](
                data=[],
                pager=Pager(pageNo=page_no, itemsPerPage=items_per_page, pagePerDisplay=5, totalNextPages=0),
            )

        raw_records = result.get("data") or []
        raw_pager = result.get("pager") or {
            "pageNo": page_no,
            "itemsPerPage": items_per_page,
            "pagePerDisplay": 5,
            "totalNextPages": 0,
        }

        records = [PriceHistoryRecord.model_validate(item) for item in raw_records]
        pager = Pager.model_validate(raw_pager)
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
                "sectorCode": sector_code.strip(),
                "limit": min(limit, 100),
            },
        )
        if not isinstance(result, list):
            return []
        return [TopMoverItem.model_validate(item) for item in result]