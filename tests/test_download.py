# tests/test_download.py
import pytest
import sys
import os
from datetime import datetime
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from reolink_aio.typings import VOD_trigger


def make_mock_vod(start_h, start_m, end_h, end_m, triggers, day=20):
    """Create a mock VOD_file object."""
    vod = MagicMock()
    vod.start_time = datetime(2026, 2, day, start_h, start_m, 0)
    vod.end_time = datetime(2026, 2, day, end_h, end_m, 0)
    vod.triggers = triggers
    vod.file_name = f"Mp4Record/2026-02-{day}/Rec_{start_h:02d}{start_m:02d}.mp4"
    vod.duration.total_seconds.return_value = (end_h - start_h) * 3600 + (end_m - start_m) * 60
    return vod


def test_filter_vods_person_only():
    from download import filter_vods
    vods = [
        make_mock_vod(10, 0, 10, 5, VOD_trigger.PERSON),
        make_mock_vod(11, 0, 11, 5, VOD_trigger.MOTION),
        make_mock_vod(12, 0, 12, 5, VOD_trigger.PERSON | VOD_trigger.MOTION),
    ]
    result = filter_vods(vods, VOD_trigger.PERSON)
    assert len(result) == 2
    assert result[0].start_time.hour == 10
    assert result[1].start_time.hour == 12


def test_filter_vods_combined_trigger():
    from download import filter_vods
    vods = [
        make_mock_vod(10, 0, 10, 5, VOD_trigger.PERSON),
        make_mock_vod(11, 0, 11, 5, VOD_trigger.VEHICLE),
        make_mock_vod(12, 0, 12, 5, VOD_trigger.PET),
    ]
    result = filter_vods(vods, VOD_trigger.PERSON | VOD_trigger.VEHICLE)
    assert len(result) == 2


def test_filter_vods_none_returns_all():
    from download import filter_vods
    vods = [
        make_mock_vod(10, 0, 10, 5, VOD_trigger.PERSON),
        make_mock_vod(11, 0, 11, 5, VOD_trigger.MOTION),
    ]
    result = filter_vods(vods, None)
    assert len(result) == 2


def test_apply_latest():
    from download import apply_latest
    vods = [
        make_mock_vod(8, 0, 8, 5, VOD_trigger.PERSON),
        make_mock_vod(10, 0, 10, 5, VOD_trigger.PERSON),
        make_mock_vod(12, 0, 12, 5, VOD_trigger.PERSON),
    ]
    result = apply_latest(vods, 2)
    assert len(result) == 2
    # Most recent first
    assert result[0].start_time.hour == 12
    assert result[1].start_time.hour == 10


def test_make_output_filename():
    from download import make_output_filename
    vod = make_mock_vod(10, 30, 10, 45, VOD_trigger.PERSON)
    name = make_output_filename(vod)
    assert name == "person_103000_104500.mp4"


def test_make_output_filename_multiple_triggers():
    from download import make_output_filename
    vod = make_mock_vod(10, 30, 10, 45, VOD_trigger.PERSON | VOD_trigger.VEHICLE)
    name = make_output_filename(vod)
    assert name.endswith(".mp4")
    assert "103000" in name
    assert "104500" in name


def test_make_output_filename_motion():
    from download import make_output_filename
    vod = make_mock_vod(14, 0, 14, 10, VOD_trigger.MOTION)
    name = make_output_filename(vod)
    assert name == "motion_140000_141000.mp4"
