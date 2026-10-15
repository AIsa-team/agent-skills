"""Date utilities for last30days skill."""

import calendar
import math
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Optional, Tuple


def get_date_range(days: int = 30) -> Tuple[str, str]:
    """Get the date range for the last N days.

    Returns:
        Tuple of (from_date, to_date) as YYYY-MM-DD strings
    """
    today = datetime.now(timezone.utc).date()
    from_date = today - timedelta(days=days)
    return from_date.isoformat(), today.isoformat()


def parse_date(date_str: Optional[str], *, reference_time: Optional[datetime] = None) -> Optional[datetime]:
    """Parse a date string in various formats.

    Supports: Unix timestamp, ISO 8601, YYYY-MM-DD, and RFC 2822 / HTTP-date
    (e.g. 'Wed, 15 Apr 2026 19:28:36 GMT') — the format used by Tavily and
    many news sources via published_date.
    """
    if date_str is None or isinstance(date_str, bool):
        return None
    date_str = str(date_str).strip()
    if not date_str:
        return None
    date_str = re.sub(r"^(?:streamed|premiered)\s+", "", date_str, flags=re.IGNORECASE)
    relative = re.fullmatch(r"(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago", date_str, re.IGNORECASE)
    if relative:
        reference = reference_time or datetime.now(timezone.utc)
        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=timezone.utc)
        reference = reference.astimezone(timezone.utc)
        quantity, unit = int(relative[1]), relative[2].lower()
        try:
            if unit in {"month", "year"}:
                month_index = reference.year * 12 + reference.month - 1 - quantity * (12 if unit == "year" else 1)
                year, month = divmod(month_index, 12)
                month += 1
                return reference.replace(year=year, month=month, day=min(reference.day, calendar.monthrange(year, month)[1]))
            seconds = quantity * {"second": 1, "minute": 60, "hour": 3600, "day": 86400, "week": 604800}[unit]
            return reference - timedelta(seconds=seconds)
        except (ValueError, OverflowError):
            return None

    # Try Unix timestamp (from Reddit)
    try:
        ts = float(date_str)
        if not math.isfinite(ts):
            return None
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except (ValueError, TypeError, OverflowError, OSError):
        pass

    # Try ISO formats
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%a %b %d %H:%M:%S %z %Y",
        "%b %d, %Y",
        "%B %d, %Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is not None:
                return dt.astimezone(timezone.utc)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    # Try RFC 2822 / HTTP-date (e.g. 'Wed, 15 Apr 2026 19:28:36 GMT').
    # parsedate_to_datetime returns None for unparseable input on 3.10+, but
    # on some inputs raises TypeError/ValueError — guard both paths.
    try:
        dt = parsedate_to_datetime(date_str)
    except (TypeError, ValueError):
        return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def timestamp_to_date(ts: Optional[float]) -> Optional[str]:
    """Convert Unix timestamp to YYYY-MM-DD string."""
    if ts is None:
        return None
    try:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.date().isoformat()
    except (ValueError, TypeError, OSError, OverflowError):
        return None


def get_date_confidence(date_str: Optional[str], from_date: str, to_date: str) -> str:
    """Determine confidence level for a date.

    Args:
        date_str: The date to check (YYYY-MM-DD or None)
        from_date: Start of valid range (YYYY-MM-DD)
        to_date: End of valid range (YYYY-MM-DD)

    Returns:
        'high', 'med', or 'low'
    """
    if not date_str:
        return 'low'

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").date()
        start = datetime.strptime(from_date, "%Y-%m-%d").date()
        end = datetime.strptime(to_date, "%Y-%m-%d").date()

        return 'high' if start <= dt <= end else 'low'
    except ValueError:
        return 'low'


def days_ago(date_str: Optional[str]) -> Optional[int]:
    """Calculate how many days ago a date is.

    Returns None if date is invalid or missing.
    """
    if not date_str:
        return None

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now(timezone.utc).date()
        delta = today - dt
        return delta.days
    except ValueError:
        return None


def recency_score(date_str: Optional[str], max_days: int = 30) -> int:
    """Calculate recency score (0-100).

    0 days ago = 100, max_days ago = 0, clamped.
    """
    age = days_ago(date_str)
    if age is None:
        return 0  # Unknown date gets worst score

    if age < 0:
        return 100  # Future date (treat as today)
    if age >= max_days:
        return 0

    return int(100 * (1 - age / max_days))
