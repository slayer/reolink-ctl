"""Time parsing utilities extracted from download.py."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Optional


def parse_since(since_str: str) -> tuple[datetime, datetime]:
    """Parse relative time like '30m', '2h', '3d' into (start, end) datetimes."""
    match = re.fullmatch(r"(\d+)([mhd])", since_str)
    if not match:
        raise ValueError(f"Invalid --since format: {since_str!r}. Use e.g. 30m, 2h, 3d")

    amount = int(match.group(1))
    if amount <= 0:
        raise ValueError(f"Invalid --since value: must be > 0, got {since_str!r}")
    unit = match.group(2)
    multiplier = {"m": 60, "h": 3600, "d": 86400}[unit]

    end = datetime.now()
    start = end - timedelta(seconds=amount * multiplier)
    return start, end


def parse_date_range(
    date_str: Optional[str],
    from_str: Optional[str],
    to_str: Optional[str],
) -> tuple[datetime, datetime]:
    """Parse --date or --from/--to into (start, end) datetimes."""
    if date_str:
        if date_str == "today":
            d = date.today()
        elif date_str == "yesterday":
            d = date.today() - timedelta(days=1)
        else:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (
            datetime(d.year, d.month, d.day, 0, 0, 0),
            datetime(d.year, d.month, d.day, 23, 59, 59),
        )

    if from_str and to_str:
        start_d = datetime.strptime(from_str, "%Y-%m-%d").date()
        end_d = datetime.strptime(to_str, "%Y-%m-%d").date()
        return (
            datetime(start_d.year, start_d.month, start_d.day, 0, 0, 0),
            datetime(end_d.year, end_d.month, end_d.day, 23, 59, 59),
        )

    # Default: today
    d = date.today()
    return (
        datetime(d.year, d.month, d.day, 0, 0, 0),
        datetime(d.year, d.month, d.day, 23, 59, 59),
    )
