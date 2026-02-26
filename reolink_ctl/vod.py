"""VOD (Video on Demand) trigger parsing and filtering, extracted from download.py."""

from __future__ import annotations

from typing import Optional

from reolink_aio.typings import VOD_trigger


# -- Trigger name mapping for filenames --
TRIGGER_NAMES = {
    VOD_trigger.PERSON: "person",
    VOD_trigger.VEHICLE: "vehicle",
    VOD_trigger.PET: "pet",
    VOD_trigger.MOTION: "motion",
}


def build_trigger_filter(
    *,
    person: bool,
    vehicle: bool,
    pet: bool,
    motion: bool,
    all_triggers: bool,
) -> Optional[VOD_trigger]:
    """Build a VOD_trigger filter from CLI flags. Returns None if no filter (= all)."""
    if all_triggers:
        return None

    trigger = VOD_trigger.NONE
    if person:
        trigger |= VOD_trigger.PERSON
    if vehicle:
        trigger |= VOD_trigger.VEHICLE
    if pet:
        trigger |= VOD_trigger.PET
    if motion:
        trigger |= VOD_trigger.MOTION

    return trigger if trigger != VOD_trigger.NONE else None


def parse_triggers_from_filename(filename: str) -> VOD_trigger:
    """Parse trigger flags from recording filename hex field.

    Handles both old (7-char hex like '6D28808') and new (10-char hex like
    '6D28808000') filename formats. The library's built-in parser (v0.9.0)
    doesn't recognize the newer 7-part filename format, so we do it here.

    Trigger nibble layout (same for both formats, at fixed offset after prefix):
      nibble T: bit 2 = Person, bit 0 = Vehicle
      nibble t: bit 3 = Pet,    bit 0 = Timer
      nibble r: bit 3 = Motion
    """
    basename = filename.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    parts = basename.split("_")

    if len(parts) < 6:
        return VOD_trigger.NONE

    hex_field = parts[-2]

    if len(hex_field) < 7:
        return VOD_trigger.NONE

    try:
        nib_t = int(hex_field[4], 16)
        nib_u = int(hex_field[5], 16)
        nib_r = int(hex_field[6], 16)
    except (ValueError, IndexError):
        return VOD_trigger.NONE

    triggers = VOD_trigger.NONE
    if nib_t & 4:
        triggers |= VOD_trigger.PERSON
    if nib_t & 1:
        triggers |= VOD_trigger.VEHICLE
    if nib_u & 8:
        triggers |= VOD_trigger.PET
    if nib_u & 1:
        triggers |= VOD_trigger.TIMER
    if nib_r & 8:
        triggers |= VOD_trigger.MOTION

    return triggers


def get_vod_triggers(vod) -> VOD_trigger:
    """Get triggers for a VOD file, falling back to our own filename parser."""
    triggers = vod.triggers
    if triggers == VOD_trigger.NONE:
        triggers = parse_triggers_from_filename(vod.file_name)
    return triggers


def filter_vods(vods: list, trigger_filter: VOD_trigger | None) -> list:
    """Filter VOD files by trigger type. None means no filter."""
    if trigger_filter is None:
        return list(vods)
    return [v for v in vods if get_vod_triggers(v) & trigger_filter]


def apply_latest(vods: list, latest: int | None) -> list:
    """Sort by start_time descending and take the latest N."""
    if latest is None:
        return vods
    sorted_vods = sorted(vods, key=lambda v: v.start_time, reverse=True)
    return sorted_vods[:latest]


def get_primary_trigger_name(triggers: VOD_trigger) -> str:
    """Get a human-readable name for the primary trigger."""
    for trigger_val, name in TRIGGER_NAMES.items():
        if triggers & trigger_val:
            return name
    return "recording"


def make_output_filename(vod) -> str:
    """Generate output filename like 'person_103000_104500.mp4'."""
    trigger_name = get_primary_trigger_name(get_vod_triggers(vod))
    start = vod.start_time.strftime("%H%M%S")
    end = vod.end_time.strftime("%H%M%S")
    return f"{trigger_name}_{start}_{end}.mp4"
