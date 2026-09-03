"""Tests for NepseAPIClient using respx HTTP mocks."""

import pytest
import respx
import httpx

from nepse_mcp.client import NepseAPIClient
from nepse_mcp.utils import NepseAPIError


# ── Sample payloads (trimmed from API docs) ──────────────────────────────────

COMPANIES_RESPONSE = {
    "statusCode": 200,
    "message": "Success",
    "result": [
        {
            "companyId": 1,
            "companyName": "Agricultural Development Bank Limited",
            "stockSymbol": "ADBL",
            "sectorId": 0,
            "sectorName": "Commercial Banks",
        }
    ],
}

STOCK_LIVE_RESPONSE = {
    "statusCode": 200,
    "message": "Success",
    "result": {
        "stocks": [
            {
                "stockSymbol": "ADBL",
                "companyName": "Agricultural Development Bank Limited",
                "noOfTransactions": 50,
                "maxPrice": 500.0,
                "minPrice": 490.0,
                "openingPrice": 492.0,
                "closingPrice": 498.5,
                "amount": 1000000.0,
                "previousClosing": 495.0,
                "differenceRs": 3.5,
                "percentChange": 0.71,
                "volume": 2000,
                "ltv": 0,
                "asOfDate": "2026-09-03T15:00:00",
                "asOfDateString": "As of Thu, 03 Sep 2026 | 03:00:00 PM",
                "tradeDate": "2026-09-03",
                "dataType": None,
            }
        ],
        "summary": {
            "totalAmount": 3465201042.79,
            "totalShares": 12163763,
            "totalTxns": 40692,
        },
    },
}

DIVIDEND_RESPONSE = {
    "statusCode": 200,
    "message": "Success",
    "result": {
        "data": [
            {
                "sn": 1,
                "companyName": "Agricultural Development Bank Limited",
                "stockSymbol": "ADBL",
                "bonus": "10.00",
                "cash": "5.00",
                "totalDividend": "15.00",
                "bookClosureDateAD": "2022-03-31",
                "bookClosureDateBS": "2078-12-17",
                "fiscalYearAD": "2020/2021",
                "fiscalYearBS": "2077/2078",
                "rightShare": None,
                "rightBookCloseDateAD": None,
                "rightBookCloseDateBS": None,
            }
        ],
        "pager": {
            "pageNo": 1,
            "itemsPerPage": 20,
            "pagePerDisplay": 5,
            "totalNextPages": 0,
        },
    },
}

PRICE_HISTORY_RESPONSE = {
    "statusCode": 200,
    "message": "Success",
    "result": {
        "data": [
            {
                "sn": 1,
                "tradeDate": "2026-09-03T00:00:00",
                "tradeDateString": "2026-09-03",
                "maxPrice": 500.0,
                "minPrice": 490.0,
                "closingPrice": 498.5,
                "noOfTransactions": 50,
                "volume": 2000,
                "amount": 1000000.0,
                "previousClosing": 495.0,
                "differenceRs": 3.5,
                "percentChange": 0.71,
            }
        ],
        "pager": {
            "pageNo": 1,
            "itemsPerPage": 20,
            "pagePerDisplay": 5,
            "totalNextPages": 2,
        },
    },
}

TOP_MOVERS_RESPONSE = {
    "statusCode": 200,
    "message": "Success",
    "result": [
        {
            "stockSymbol": "WNLB",
            "companyName": "Wean Nepal Laghubitta",
            "noOfTransactions": 79,
            "maxPrice": 1099.0,
            "minPrice": 971.1,
            "openingPrice": 971.1,
            "closingPrice": 1055.0,
            "amount": 2136884.2,
            "previousClosing": 970.0,
            "differenceRs": 85.0,
            "percentChange": 8.76,
            "volume": 2068,
            "ltv": 0,
            "asOfDate": "2026-09-03T15:00:00",
            "asOfDateString": "As of Thu, 03 Sep 2026 | 03:00:00 PM",
            "tradeDate": "2026-09-03",
            "dataType": "gainer",
        }
    ],
}

ERROR_BODY_RESPONSE = {
    "statusCode": 400,
    "message": "Bad Request",
    "result": None,
}


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_companies_happy_path():
    with respx.mock:
        respx.get("https://nepalipaisa.com/api/GetCompanies").mock(
            return_value=httpx.Response(200, json=COMPANIES_RESPONSE)
        )
        async with NepseAPIClient() as client:
            companies = await client.get_companies()

    assert len(companies) == 1
    assert companies[0].stockSymbol == "ADBL"
    assert companies[0].sectorName == "Commercial Banks"


@pytest.mark.asyncio
async def test_get_stock_live_happy_path():
    with respx.mock:
        respx.get("https://nepalipaisa.com/api/GetStockLive").mock(
            return_value=httpx.Response(200, json=STOCK_LIVE_RESPONSE)
        )
        async with NepseAPIClient() as client:
            result = await client.get_stock_live(stock_symbol="ADBL")

    assert len(result.stocks) == 1
    assert result.stocks[0].stockSymbol == "ADBL"
    assert result.stocks[0].closingPrice == 498.5
    assert result.summary is not None
    assert result.summary.totalTxns == 40692


@pytest.mark.asyncio
async def test_get_dividend_rights_happy_path():
    with respx.mock:
        respx.get("https://nepalipaisa.com/api/GetDividendRights").mock(
            return_value=httpx.Response(200, json=DIVIDEND_RESPONSE)
        )
        async with NepseAPIClient() as client:
            page = await client.get_dividend_rights(stock_symbol="ADBL")

    assert len(page.data) == 1
    record = page.data[0]
    assert record.stockSymbol == "ADBL"
    # Verify string → float conversion
    assert record.bonus == 10.0
    assert record.cash == 5.0
    assert record.totalDividend == 15.0
    assert page.pager.totalNextPages == 0


@pytest.mark.asyncio
async def test_get_stock_history_happy_path():
    with respx.mock:
        respx.get("https://nepalipaisa.com/api/GetStockHistory").mock(
            return_value=httpx.Response(200, json=PRICE_HISTORY_RESPONSE)
        )
        async with NepseAPIClient() as client:
            page = await client.get_stock_history(
                stock_symbol="ADBL",
                from_date="2026-08-03",
                to_date="2026-09-03",
            )

    assert len(page.data) == 1
    assert page.data[0].closingPrice == 498.5
    # has_more_data flag logic (totalNextPages == 2 → True)
    assert page.pager.totalNextPages == 2


@pytest.mark.asyncio
async def test_get_top_market_movers_happy_path():
    with respx.mock:
        respx.get("https://nepalipaisa.com/api/GetTopMarketMovers").mock(
            return_value=httpx.Response(200, json=TOP_MOVERS_RESPONSE)
        )
        async with NepseAPIClient() as client:
            movers = await client.get_top_market_movers(indicator="gainers")

    assert len(movers) == 1
    assert movers[0].stockSymbol == "WNLB"
    assert movers[0].dataType == "gainer"


@pytest.mark.asyncio
async def test_non_200_status_code_in_body_raises_error():
    with respx.mock:
        respx.get("https://nepalipaisa.com/api/GetCompanies").mock(
            return_value=httpx.Response(200, json=ERROR_BODY_RESPONSE)
        )
        async with NepseAPIClient() as client:
            with pytest.raises(NepseAPIError, match="statusCode=400"):
                await client.get_companies()


@pytest.mark.asyncio
async def test_http_error_raises_nepse_api_error():
    with respx.mock:
        respx.get("https://nepalipaisa.com/api/GetCompanies").mock(
            return_value=httpx.Response(500)
        )
        async with NepseAPIClient() as client:
            with pytest.raises(NepseAPIError, match="HTTP 500"):
                await client.get_companies()


@pytest.mark.asyncio
async def test_timeout_raises_nepse_api_error():
    with respx.mock:
        respx.get("https://nepalipaisa.com/api/GetCompanies").mock(
            side_effect=httpx.TimeoutException("timed out")
        )
        async with NepseAPIClient() as client:
            with pytest.raises(NepseAPIError, match="timed out"):
                await client.get_companies()
