# tests/test_cli.py
import pytest
from datetime import datetime, date, timedelta
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_parse_since_minutes():
    from download import parse_since
    start, end = parse_since("30m")
    assert (end - start).total_seconds() == pytest.approx(30 * 60, abs=2)


def test_parse_since_hours():
    from download import parse_since
    start, end = parse_since("2h")
    assert (end - start).total_seconds() == pytest.approx(2 * 3600, abs=2)


def test_parse_since_days():
    from download import parse_since
    start, end = parse_since("3d")
    assert (end - start).total_seconds() == pytest.approx(3 * 86400, abs=2)


def test_parse_since_invalid():
    from download import parse_since
    with pytest.raises(ValueError):
        parse_since("10x")


def test_parse_date_today():
    from download import parse_date_range
    start, end = parse_date_range("today", None, None)
    today = date.today()
    assert start.date() == today
    assert end.date() == today
    assert start.hour == 0 and start.minute == 0
    assert end.hour == 23 and end.minute == 59


def test_parse_date_yesterday():
    from download import parse_date_range
    start, end = parse_date_range("yesterday", None, None)
    yesterday = date.today() - timedelta(days=1)
    assert start.date() == yesterday


def test_parse_date_specific():
    from download import parse_date_range
    start, end = parse_date_range("2026-02-15", None, None)
    assert start == datetime(2026, 2, 15, 0, 0, 0)
    assert end == datetime(2026, 2, 15, 23, 59, 59)


def test_parse_date_range_from_to():
    from download import parse_date_range
    start, end = parse_date_range(None, "2026-02-15", "2026-02-18")
    assert start == datetime(2026, 2, 15, 0, 0, 0)
    assert end == datetime(2026, 2, 18, 23, 59, 59)


def test_build_trigger_filter_person():
    from download import build_trigger_filter
    from reolink_aio.typings import VOD_trigger
    trigger = build_trigger_filter(person=True, vehicle=False, pet=False,
                                    motion=False, all_triggers=False)
    assert trigger & VOD_trigger.PERSON


def test_build_trigger_filter_combined():
    from download import build_trigger_filter
    from reolink_aio.typings import VOD_trigger
    trigger = build_trigger_filter(person=True, vehicle=True, pet=False,
                                    motion=False, all_triggers=False)
    assert trigger & VOD_trigger.PERSON
    assert trigger & VOD_trigger.VEHICLE


def test_build_trigger_filter_all_returns_none():
    from download import build_trigger_filter
    trigger = build_trigger_filter(person=False, vehicle=False, pet=False,
                                    motion=False, all_triggers=True)
    assert trigger is None


def test_build_trigger_filter_none_selected_returns_none():
    """No flags selected = no filter = return all."""
    from download import build_trigger_filter
    trigger = build_trigger_filter(person=False, vehicle=False, pet=False,
                                    motion=False, all_triggers=False)
    assert trigger is None


def test_parse_since_zero():
    from download import parse_since
    with pytest.raises(ValueError):
        parse_since("0m")
