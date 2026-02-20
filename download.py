# download.py
"""Download Reolink camera recordings filtered by AI detection type."""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from reolink_aio.typings import VOD_trigger


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

    # No flags selected = no filter
    return trigger if trigger != VOD_trigger.NONE else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download Reolink camera recordings filtered by AI detection type.",
    )

    # Connection
    conn = parser.add_argument_group("connection")
    conn.add_argument("-H", "--host", help="Camera IP (env: REOLINK_HOST)")
    conn.add_argument("-u", "--user", help="Username (env: REOLINK_USER)")
    conn.add_argument("-p", "--password", help="Password (env: REOLINK_PASSWORD)")

    # Trigger filters — only types supported by installed reolink_aio
    triggers = parser.add_argument_group("trigger filters")
    triggers.add_argument("--person", action="store_true", help="Person detection")
    triggers.add_argument("--vehicle", action="store_true", help="Vehicle detection")
    triggers.add_argument("--pet", action="store_true", help="Pet/animal detection")
    triggers.add_argument("--motion", action="store_true", help="Motion detection")
    triggers.add_argument("--all", dest="all_triggers", action="store_true",
                          help="All trigger types (default if none selected)")

    # Time selection
    time = parser.add_argument_group("time selection")
    time.add_argument("--date", dest="date", help="Specific date: YYYY-MM-DD, 'today', 'yesterday'")
    time.add_argument("--from", dest="from_date", help="Range start: YYYY-MM-DD")
    time.add_argument("--to", dest="to_date", help="Range end: YYYY-MM-DD")
    time.add_argument("--since", help="Relative period: 30m, 2h, 1d, 3d")
    time.add_argument("--latest", type=int, help="Limit to N most recent recordings")

    # Output
    output = parser.add_argument_group("output")
    output.add_argument("--output-dir", default="./downloads", help="Download directory (default: ./downloads)")
    output.add_argument("--dry-run", action="store_true", help="List files without downloading")
    output.add_argument("--stream", choices=["main", "sub"], default="main", help="Stream quality (default: main)")

    return parser


def resolve_config(args: argparse.Namespace) -> dict:
    """Resolve config from CLI args + .env fallback."""
    load_dotenv()
    return {
        "host": args.host or os.getenv("REOLINK_HOST"),
        "user": args.user or os.getenv("REOLINK_USER", "admin"),
        "password": args.password or os.getenv("REOLINK_PASSWORD"),
    }


# -- Trigger name mapping for filenames --
# Only includes members that exist in this version of reolink_aio
TRIGGER_NAMES = {
    VOD_trigger.PERSON: "person",
    VOD_trigger.VEHICLE: "vehicle",
    VOD_trigger.PET: "pet",
    VOD_trigger.MOTION: "motion",
}


def filter_vods(vods: list, trigger_filter: VOD_trigger | None) -> list:
    """Filter VOD files by trigger type. None means no filter."""
    if trigger_filter is None:
        return list(vods)
    return [v for v in vods if v.triggers & trigger_filter]


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
    trigger_name = get_primary_trigger_name(vod.triggers)
    start = vod.start_time.strftime("%H%M%S")
    end = vod.end_time.strftime("%H%M%S")
    return f"{trigger_name}_{start}_{end}.mp4"


async def run(
    *,
    config: dict,
    start: datetime,
    end: datetime,
    trigger_filter: Optional[VOD_trigger],
    latest: Optional[int],
    output_dir: Path,
    dry_run: bool,
    stream: str,
):
    """Stub -- implemented in Task 4."""
    raise NotImplementedError("run() not yet implemented")


def main():
    parser = build_parser()
    args = parser.parse_args()
    config = resolve_config(args)

    if not config["host"]:
        parser.error("Camera host required: use --host or set REOLINK_HOST in .env")
    if not config["password"]:
        parser.error("Password required: use --password or set REOLINK_PASSWORD in .env")

    if (args.from_date or args.to_date) and not (args.from_date and args.to_date):
        parser.error("--from and --to must be used together")
    if args.since and (args.date or args.from_date):
        parser.error("--since cannot be combined with --date or --from/--to")

    # Determine time range
    if args.since:
        start, end = parse_since(args.since)
    else:
        start, end = parse_date_range(args.date, args.from_date, args.to_date)

    trigger_filter = build_trigger_filter(
        person=args.person,
        vehicle=args.vehicle,
        pet=args.pet,
        motion=args.motion,
        all_triggers=args.all_triggers,
    )

    asyncio.run(run(
        config=config,
        start=start,
        end=end,
        trigger_filter=trigger_filter,
        latest=args.latest,
        output_dir=Path(args.output_dir),
        dry_run=args.dry_run,
        stream=args.stream,
    ))


if __name__ == "__main__":
    main()
