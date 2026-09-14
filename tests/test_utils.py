import pytest
from nepse_mcp.schemas import PriceHistorySummary
from nepse_mcp.utils import (
    NepseAPIError,
    build_tool_response,
    summarize_history_gaps,
    validate_date_format,
)


def test_valid_date_passes():
    validate_date_format("2026-09-03")  # should not raise


def test_valid_date_leap_day_passes():
    validate_date_format("2024-02-29")  # 2024 is a leap year


def test_invalid_format_raises():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        validate_date_format("03-09-2026")


def test_invalid_format_no_separators_raises():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        validate_date_format("20260903")


def test_invalid_month_raises():
    with pytest.raises(ValueError):
        validate_date_format("2026-13-01")


def test_invalid_day_raises():
    with pytest.raises(ValueError):
        validate_date_format("2026-02-30")


def test_non_leap_year_feb29_raises():
    with pytest.raises(ValueError):
        validate_date_format("2023-02-29")


def test_nepse_api_error_message():
    err = NepseAPIError("Something went wrong")
    assert str(err) == "Something went wrong"
    assert err.message == "Something went wrong"


def test_build_tool_response_success_envelope():
    payload = build_tool_response(data={"stockSymbol": "ADBL"})
    assert payload == {
        "status": "success",
        "data": {"stockSymbol": "ADBL"},
        "data_complete": True,
        "warning": None,
        "source_gap_detected": False,
    }


def test_build_tool_response_error_envelope():
    payload = build_tool_response(
        status="error",
        error_message="Timed out",
    )
    assert payload["status"] == "error"
    assert payload["error_message"] == "Timed out"
    assert payload["data_complete"] is False
    assert payload["warning"] is None
    assert payload["source_gap_detected"] is False


def test_summarize_history_gaps_marks_incomplete_metrics():
    summary = PriceHistorySummary(
        stockSymbol="ADBL",
        fromDate="2026-08-01",
        toDate="2026-08-03",
        recordCount=3,
        firstClose=100.0,
        lastClose=110.0,
        absoluteReturn=10.0,
        percentReturn=10.0,
        highestClose=110.0,
        lowestClose=100.0,
        dayChange=5.0,
        dayChangePercent=4.76,
        sevenDayReturn=None,
        thirtyDayReturn=None,
        sma5=None,
        sma10=None,
        sma20=None,
        maxDrawdown=0.0,
        averageVolume=1233.33,
        averageTurnover=129833.33,
        volatility=1.5,
        volumeTrend="insufficient_data",
        trend="uptrend",
    )
    data_complete, source_gap_detected, warning = summarize_history_gaps(summary)
    assert data_complete is False
    assert source_gap_detected is True
    assert warning is not None
    assert "SMA" in warning
