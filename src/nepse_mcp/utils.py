import re
from datetime import datetime
from typing import Any, Optional

from nepse_mcp.schemas import (
    BaseMarketItem,
    CompactDividendRecord,
    CompactLiveMarketResult,
    CompactLiveStock,
    CompactMarketSummary,
    CompactPriceHistoryRecord,
    DividendRecord,
    LiveMarketResult,
    PriceHistoryRecord,
    PriceHistorySummary,
)


class NepseAPIError(Exception):
    """Raised when the NEPSE API returns an error or is unreachable."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self) -> str:
        if self.status_code:
            return f"[HTTP {self.status_code}] {self.message}"
        return self.message


_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_date_format(date_str: str) -> None:
    """Validate that a string is a valid YYYY-MM-DD date.

    Raises:
        ValueError: If the string is not a valid date, with an actionable
            error message designed to help an LLM self-correct.
    """
    # Guard against LLMs hallucinating non-string types (e.g., passing a dict or None)
    if not isinstance(date_str, str):
        raise ValueError(
            f"Invalid type: Expected a string for date, got {type(date_str).__name__}."
        )

    date_str = date_str.strip()

    # 1. Check structural format first
    if not _DATE_PATTERN.match(date_str):
        raise ValueError(
            f"Invalid date format: '{date_str}'. "
            "You must strictly use the YYYY-MM-DD format (e.g., '2026-09-04')."
        )

    # 2. Check calendar validity (e.g., catching Feb 30th or Month 13)
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"Impossible date value: '{date_str}'. "
            "The YYYY-MM-DD format is correct, but this specific date does not exist "
            "on the calendar (check month length and leap years). Please correct it."
        )


def build_tool_response(
    *,
    data: Any = None,
    status: str = "success",
    data_complete: bool = True,
    warning: str | None = None,
    source_gap_detected: bool = False,
    error_message: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Build a stable MCP tool response envelope with completeness metadata."""
    if status == "error":
        return {
            "status": "error",
            "error_message": error_message or "Unknown error",
            "data_complete": False,
            "warning": warning,
            "source_gap_detected": source_gap_detected,
            **extra,
        }

    payload: dict[str, Any] = {
        "status": "success",
        "data_complete": data_complete,
        "warning": warning,
        "source_gap_detected": source_gap_detected,
        **extra,
    }
    if data is not None:
        payload["data"] = data
    return payload


def summarize_history_gaps(
    summary: PriceHistorySummary,
) -> tuple[bool, bool, str | None]:
    """Detect incomplete analytics caused by short price history."""
    missing: list[str] = []
    if summary.sevenDayReturn is None:
        missing.append("7-day return")
    if summary.thirtyDayReturn is None:
        missing.append("30-day return")
    if summary.sma5 is None:
        missing.append("SMA5")
    if summary.sma10 is None:
        missing.append("SMA10")
    if summary.sma20 is None:
        missing.append("SMA20")
    if summary.volumeTrend == "insufficient_data":
        missing.append("volume trend")
    if summary.trend == "insufficient_data":
        missing.append("trend")

    if not missing:
        return True, False, None

    warning = (
        "Incomplete history for requested window: "
        f"{', '.join(missing)} unavailable "
        f"(only {summary.recordCount} trading days)."
    )
    return False, True, warning


def to_compact_live_stock(item: BaseMarketItem) -> CompactLiveStock:
    """Normalize a live/mover stock row into stable analysis-friendly fields."""
    return CompactLiveStock(
        stockSymbol=item.stockSymbol,
        companyName=item.companyName,
        closingPrice=item.closingPrice,
        previousClosing=item.previousClosing,
        dayChange=item.differenceRs,
        percentChange=item.percentChange,
        volume=item.volume,
        turnover=item.amount,
        dayHigh=item.maxPrice,
        dayLow=item.minPrice,
        openingPrice=item.openingPrice,
        noOfTransactions=item.noOfTransactions,
        tradeDate=item.tradeDate,
        asOfDate=item.asOfDate,
    )


def to_compact_live_result(result: LiveMarketResult) -> CompactLiveMarketResult:
    """Normalize a live market payload, dropping unused upstream fields."""
    summary = None
    if result.summary is not None:
        summary = CompactMarketSummary(
            totalTurnover=result.summary.totalAmount,
            totalShares=result.summary.totalShares,
            totalTxns=result.summary.totalTxns,
        )
    return CompactLiveMarketResult(
        stocks=[to_compact_live_stock(stock) for stock in result.stocks],
        summary=summary,
    )


def to_compact_price_history_record(record: PriceHistoryRecord) -> CompactPriceHistoryRecord:
    """Normalize a price-history row with stable field names."""
    return CompactPriceHistoryRecord(
        tradeDate=record.tradeDate,
        dayHigh=record.maxPrice,
        dayLow=record.minPrice,
        closingPrice=record.closingPrice,
        previousClosing=record.previousClosing,
        dayChange=record.differenceRs,
        percentChange=record.percentChange,
        volume=record.volume,
        turnover=record.amount,
        noOfTransactions=record.noOfTransactions,
    )


def to_compact_dividend_record(record: DividendRecord) -> CompactDividendRecord:
    """Normalize a dividend row, dropping noisy serial and BS date fields."""
    return CompactDividendRecord(
        companyName=record.companyName,
        stockSymbol=record.stockSymbol,
        bonus=record.bonus,
        cash=record.cash,
        totalDividend=record.totalDividend,
        bookClosureDateAD=record.bookClosureDateAD,
        fiscalYearAD=record.fiscalYearAD,
        fiscalYearBS=record.fiscalYearBS,
        rightShare=record.rightShare,
        rightBookCloseDateAD=record.rightBookCloseDateAD,
    )
