import re
from datetime import datetime
from typing import Optional


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