import re
from datetime import datetime


class NepseAPIError(Exception):
    """Raised when the NepaliPaisa API returns an error or is unreachable."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_date_format(date_str: str) -> None:
    """Validate that a string is a valid YYYY-MM-DD date.

    Raises:
        ValueError: If the string is not a valid date in YYYY-MM-DD format.
    """
    if not _DATE_PATTERN.match(date_str):
        raise ValueError(
            f"Invalid date format: {date_str!r}. Expected YYYY-MM-DD (e.g. 2026-01-31)."
        )
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"Invalid date value: {date_str!r}. "
            "Ensure month is 01-12 and day is valid for the given month."
        )
