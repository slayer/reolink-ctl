"""Tests for reolink_ctl.vod — migrated from test_download.py."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from reolink_aio.typings import VOD_trigger

from reolink_ctl.vod import (
    build_trigger_filter,
    filter_vods,
    apply_latest,
    make_output_filename,
    parse_triggers_from_filename,
    get_vod_triggers,
)
from conftest import make_vod


def test_build_trigger_filter_person():
    trigger = build_trigger_filter(person=True, vehicle=False, pet=False,
                                    motion=False, all_triggers=False)
    assert trigger & VOD_trigger.PERSON


def test_build_trigger_filter_combined():
    trigger = build_trigger_filter(person=True, vehicle=True, pet=False,
                                    motion=False, all_triggers=False)
    assert trigger & VOD_trigger.PERSON
    assert trigger & VOD_trigger.VEHICLE


def test_build_trigger_filter_all_returns_none():
    trigger = build_trigger_filter(person=False, vehicle=False, pet=False,
                                    motion=False, all_triggers=True)
    assert trigger is None


def test_build_trigger_filter_none_selected_returns_none():
    trigger = build_trigger_filter(person=False, vehicle=False, pet=False,
                                    motion=False, all_triggers=False)
    assert trigger is None


def test_filter_vods_person_only():
    vods = [
        make_vod(10, 0, 10, 5, VOD_trigger.PERSON),
        make_vod(11, 0, 11, 5, VOD_trigger.MOTION),
        make_vod(12, 0, 12, 5, VOD_trigger.PERSON | VOD_trigger.MOTION),
    ]
    result = filter_vods(vods, VOD_trigger.PERSON)
    assert len(result) == 2
    assert result[0].start_time.hour == 10
    assert result[1].start_time.hour == 12


def test_filter_vods_combined_trigger():
    vods = [
        make_vod(10, 0, 10, 5, VOD_trigger.PERSON),
        make_vod(11, 0, 11, 5, VOD_trigger.VEHICLE),
        make_vod(12, 0, 12, 5, VOD_trigger.PET),
    ]
    result = filter_vods(vods, VOD_trigger.PERSON | VOD_trigger.VEHICLE)
    assert len(result) == 2


def test_filter_vods_none_returns_all():
    vods = [
        make_vod(10, 0, 10, 5, VOD_trigger.PERSON),
        make_vod(11, 0, 11, 5, VOD_trigger.MOTION),
    ]
    result = filter_vods(vods, None)
    assert len(result) == 2


def test_apply_latest():
    vods = [
        make_vod(8, 0, 8, 5, VOD_trigger.PERSON),
        make_vod(10, 0, 10, 5, VOD_trigger.PERSON),
        make_vod(12, 0, 12, 5, VOD_trigger.PERSON),
    ]
    result = apply_latest(vods, 2)
    assert len(result) == 2
    assert result[0].start_time.hour == 12
    assert result[1].start_time.hour == 10


def test_make_output_filename():
    vod = make_vod(10, 30, 10, 45, VOD_trigger.PERSON)
    name = make_output_filename(vod)
    assert name == "person_103000_104500.mp4"


def test_make_output_filename_multiple_triggers():
    vod = make_vod(10, 30, 10, 45, VOD_trigger.PERSON | VOD_trigger.VEHICLE)
    name = make_output_filename(vod)
    assert name.endswith(".mp4")
    assert "103000" in name
    assert "104500" in name


def test_make_output_filename_motion():
    vod = make_vod(14, 0, 14, 10, VOD_trigger.MOTION)
    name = make_output_filename(vod)
    assert name == "motion_140000_141000.mp4"


# -- Filename trigger parser tests --

def test_parse_triggers_new_format_person_motion():
    fn = "Mp4Record/2026-02-20/RecM07_20260220_092535_092740_0_6D28C08000_3FECD51.mp4"
    triggers = parse_triggers_from_filename(fn)
    assert triggers & VOD_trigger.PERSON
    assert triggers & VOD_trigger.MOTION


def test_parse_triggers_new_format_motion_only():
    fn = "Mp4Record/2026-02-20/RecM07_20260220_000000_000024_0_6D28808000_E386CE.mp4"
    triggers = parse_triggers_from_filename(fn)
    assert not (triggers & VOD_trigger.PERSON)
    assert triggers & VOD_trigger.MOTION


def test_parse_triggers_new_format_no_motion():
    fn = "Mp4Record/2026-02-20/RecM07_20260220_220932_220932_0_6D28800000_AC9CE.mp4"
    triggers = parse_triggers_from_filename(fn)
    assert not (triggers & VOD_trigger.PERSON)
    assert not (triggers & VOD_trigger.MOTION)


def test_parse_triggers_old_format():
    fn = "Mp4Record/2023-05-15/RecM02_20230515_071811_071835_6D28900_13CE8C7.mp4"
    triggers = parse_triggers_from_filename(fn)
    assert triggers & VOD_trigger.VEHICLE
    assert not (triggers & VOD_trigger.PERSON)


def test_parse_triggers_vehicle():
    fn = "Mp4Record/2026-02-20/RecM07_20260220_100000_100030_0_6D28908000_ABC123.mp4"
    triggers = parse_triggers_from_filename(fn)
    assert triggers & VOD_trigger.VEHICLE
    assert triggers & VOD_trigger.MOTION


def test_parse_triggers_pet():
    fn = "Mp4Record/2026-02-20/RecM07_20260220_100000_100030_0_6D28088000_ABC123.mp4"
    triggers = parse_triggers_from_filename(fn)
    assert triggers & VOD_trigger.PET


def test_filter_vods_uses_filename_fallback():
    vod = MagicMock()
    vod.start_time = datetime(2026, 2, 20, 9, 25, 35)
    vod.end_time = datetime(2026, 2, 20, 9, 27, 40)
    vod.triggers = VOD_trigger.NONE
    vod.file_name = "Mp4Record/2026-02-20/RecM07_20260220_092535_092740_0_6D28C08000_3FECD51.mp4"

    result = filter_vods([vod], VOD_trigger.PERSON)
    assert len(result) == 1
