"""Tests for reolink_ctl.time_utils — migrated from test_cli.py."""

import pytest
from datetime import datetime, date, timedelta

from reolink_ctl.time_utils import parse_since, parse_date_range


def test_parse_since_minutes():
    start, end = parse_since("30m")
    assert (end - start).total_seconds() == pytest.approx(30 * 60, abs=2)


def test_parse_since_hours():
    start, end = parse_since("2h")
    assert (end - start).total_seconds() == pytest.approx(2 * 3600, abs=2)


def test_parse_since_days():
    start, end = parse_since("3d")
    assert (end - start).total_seconds() == pytest.approx(3 * 86400, abs=2)


def test_parse_since_invalid():
    with pytest.raises(ValueError):
        parse_since("10x")


def test_parse_since_zero():
    with pytest.raises(ValueError):
        parse_since("0m")


def test_parse_date_today():
    start, end = parse_date_range("today", None, None)
    today = date.today()
    assert start.date() == today
    assert end.date() == today
    assert start.hour == 0 and start.minute == 0
    assert end.hour == 23 and end.minute == 59


def test_parse_date_yesterday():
    start, end = parse_date_range("yesterday", None, None)
    yesterday = date.today() - timedelta(days=1)
    assert start.date() == yesterday


def test_parse_date_specific():
    start, end = parse_date_range("2026-02-15", None, None)
    assert start == datetime(2026, 2, 15, 0, 0, 0)
    assert end == datetime(2026, 2, 15, 23, 59, 59)


def test_parse_date_range_from_to():
    start, end = parse_date_range(None, "2026-02-15", "2026-02-18")
    assert start == datetime(2026, 2, 15, 0, 0, 0)
    assert end == datetime(2026, 2, 18, 23, 59, 59)


def test_parse_date_default_is_today():
    start, end = parse_date_range(None, None, None)
    today = date.today()
    assert start.date() == today
    assert end.date() == today
