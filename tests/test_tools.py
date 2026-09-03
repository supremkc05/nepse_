"""Integration tests for MCP tools and resources using the FastMCP in-process client."""

import json
import pytest
import respx
import httpx
from fastmcp import Client

# Import the mcp instance AFTER all tools/resources are registered
from nepse_mcp.main import mcp


# ── Sample payloads ──────────────────────────────────────────────────────────

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
            "totalNextPages": 0,
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


# ── Tool tests ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tool_list_contains_expected_tools():
    async with Client(mcp) as client:
        tools = await client.list_tools()
    names = {t.name for t in tools}
    assert "get_live_market_data" in names
    assert "get_dividend_history" in names
    assert "get_price_history" in names
    assert "get_top_market_movers" in names


@pytest.mark.asyncio
async def test_get_live_market_data_tool():
    with respx.mock:
        respx.get("https://nepalipaisa.com/api/GetStockLive").mock(
            return_value=httpx.Response(200, json=STOCK_LIVE_RESPONSE)
        )
        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_live_market_data", {"stock_symbol": "ADBL"}
            )

    # FastMCP serialises dict return values as JSON text content
    payload = json.loads(result.content[0].text)
    assert len(payload["stocks"]) == 1
    assert payload["stocks"][0]["stockSymbol"] == "ADBL"
    assert payload["summary"]["totalTxns"] == 40692


@pytest.mark.asyncio
async def test_get_dividend_history_tool():
    with respx.mock:
        respx.get("https://nepalipaisa.com/api/GetDividendRights").mock(
            return_value=httpx.Response(200, json=DIVIDEND_RESPONSE)
        )
        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_dividend_history", {"stock_symbol": "ADBL"}
            )

    payload = json.loads(result.content[0].text)
    assert payload["stock_symbol"] == "ADBL"
    assert payload["has_more_data"] is False
    assert payload["records"][0]["bonus"] == 10.0


@pytest.mark.asyncio
async def test_get_price_history_tool():
    with respx.mock:
        respx.get("https://nepalipaisa.com/api/GetStockHistory").mock(
            return_value=httpx.Response(200, json=PRICE_HISTORY_RESPONSE)
        )
        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_price_history",
                {
                    "stock_symbol": "ADBL",
                    "from_date": "2026-08-03",
                    "to_date": "2026-09-03",
                },
            )

    payload = json.loads(result.content[0].text)
    assert payload["stock_symbol"] == "ADBL"
    assert payload["has_more_data"] is False
    assert payload["records"][0]["closingPrice"] == 498.5


@pytest.mark.asyncio
async def test_get_price_history_invalid_date_format():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_price_history",
            {
                "stock_symbol": "ADBL",
                "from_date": "03-08-2026",  # wrong format
                "to_date": "2026-09-03",
            },
        )

    payload = json.loads(result.content[0].text)
    assert "error" in payload
    assert "YYYY-MM-DD" in payload["error"]


@pytest.mark.asyncio
async def test_get_top_market_movers_tool():
    with respx.mock:
        respx.get("https://nepalipaisa.com/api/GetTopMarketMovers").mock(
            return_value=httpx.Response(200, json=TOP_MOVERS_RESPONSE)
        )
        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_top_market_movers", {"indicator": "gainers"}
            )

    payload = json.loads(result.content[0].text)
    assert payload["indicator"] == "gainers"
    assert payload["count"] == 1
    assert payload["movers"][0]["stockSymbol"] == "WNLB"


# ── Resource tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_companies_resource_is_listed():
    async with Client(mcp) as client:
        resources = await client.list_resources()
    uris = [str(r.uri) for r in resources]
    assert "nepse://companies" in uris


@pytest.mark.asyncio
async def test_companies_resource_returns_data():
    with respx.mock:
        respx.get("https://nepalipaisa.com/api/GetCompanies").mock(
            return_value=httpx.Response(200, json=COMPANIES_RESPONSE)
        )
        async with Client(mcp) as client:
            contents = await client.read_resource("nepse://companies")

    data = json.loads(contents[0].text)
    assert isinstance(data, list)
    assert data[0]["stockSymbol"] == "ADBL"


# ── Prompt tests ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_prompt_is_listed():
    async with Client(mcp) as client:
        prompts = await client.list_prompts()
    names = {p.name for p in prompts}
    assert "analyze_nepse_stock" in names


@pytest.mark.asyncio
async def test_prompt_returns_messages():
    async with Client(mcp) as client:
        result = await client.get_prompt(
            "analyze_nepse_stock", {"ticker": "NABIL"}
        )
    assert len(result.messages) >= 1
    assert result.messages[0].role == "user"
    # Check that the ticker appears in the prompt content
    content = result.messages[0].content
    text = content.text if hasattr(content, "text") else str(content)
    assert "NABIL" in text
