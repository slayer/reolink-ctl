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


# -- Tests for custom filename trigger parser --

def test_parse_triggers_new_format_person_motion():
    """New 10-char hex format: 6D28C08000 = Person + Motion."""
    from download import parse_triggers_from_filename
    fn = "Mp4Record/2026-02-20/RecM07_20260220_092535_092740_0_6D28C08000_3FECD51.mp4"
    triggers = parse_triggers_from_filename(fn)
    assert triggers & VOD_trigger.PERSON
    assert triggers & VOD_trigger.MOTION


def test_parse_triggers_new_format_motion_only():
    """New format: 6D28808000 = Motion only."""
    from download import parse_triggers_from_filename
    fn = "Mp4Record/2026-02-20/RecM07_20260220_000000_000024_0_6D28808000_E386CE.mp4"
    triggers = parse_triggers_from_filename(fn)
    assert not (triggers & VOD_trigger.PERSON)
    assert triggers & VOD_trigger.MOTION


def test_parse_triggers_new_format_no_motion():
    """New format: 6D28800000 = no triggers (scheduled)."""
    from download import parse_triggers_from_filename
    fn = "Mp4Record/2026-02-20/RecM07_20260220_220932_220932_0_6D28800000_AC9CE.mp4"
    triggers = parse_triggers_from_filename(fn)
    assert not (triggers & VOD_trigger.PERSON)
    assert not (triggers & VOD_trigger.MOTION)


def test_parse_triggers_old_format():
    """Old 7-char hex format: 6D28900 -> nibbles 9,0,0 -> Person + Motion."""
    from download import parse_triggers_from_filename
    fn = "Mp4Record/2023-05-15/RecM02_20230515_071811_071835_6D28900_13CE8C7.mp4"
    triggers = parse_triggers_from_filename(fn)
    # nibble '9' = 1001 -> bit 3 (0x8) is set but not mapped, bit 0 (0x1) = Vehicle
    # Actually '9' at position 4: nib_t=9=1001, bit 2 (0x4) not set so no Person
    # Wait: '9' = 1001 -> & 4 = 0 (no person), & 1 = 1 (vehicle)
    assert triggers & VOD_trigger.VEHICLE
    assert not (triggers & VOD_trigger.PERSON)


def test_parse_triggers_vehicle():
    """Hex with vehicle bit set: nibble 4 bit 0."""
    from download import parse_triggers_from_filename
    fn = "Mp4Record/2026-02-20/RecM07_20260220_100000_100030_0_6D28908000_ABC123.mp4"
    triggers = parse_triggers_from_filename(fn)
    # nibble 4 = '9' = 1001 -> bit 0 = Vehicle, bit 2 not set = no Person
    assert triggers & VOD_trigger.VEHICLE
    assert triggers & VOD_trigger.MOTION


def test_parse_triggers_pet():
    """Hex with pet bit set: nibble 5 bit 3."""
    from download import parse_triggers_from_filename
    fn = "Mp4Record/2026-02-20/RecM07_20260220_100000_100030_0_6D28088000_ABC123.mp4"
    triggers = parse_triggers_from_filename(fn)
    # nibble 5 = '8' = 1000 -> bit 3 = Pet
    assert triggers & VOD_trigger.PET


def test_filter_vods_uses_filename_fallback():
    """When library returns NONE, filter_vods falls back to filename parsing."""
    from download import filter_vods
    vod = MagicMock()
    vod.start_time = datetime(2026, 2, 20, 9, 25, 35)
    vod.end_time = datetime(2026, 2, 20, 9, 27, 40)
    vod.triggers = VOD_trigger.NONE  # Library couldn't parse
    vod.file_name = "Mp4Record/2026-02-20/RecM07_20260220_092535_092740_0_6D28C08000_3FECD51.mp4"

    result = filter_vods([vod], VOD_trigger.PERSON)
    assert len(result) == 1
