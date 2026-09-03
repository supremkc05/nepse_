import pytest
from nepse_mcp.utils import NepseAPIError, validate_date_format


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
