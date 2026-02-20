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
from reolink_aio.api import Host
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
    triggers.add_argument("--vehicle", "--car", action="store_true", help="Vehicle/car detection")
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
    output.add_argument("--verbose", "-v", action="store_true", help="Show detailed info (filenames, trigger flags)")
    output.add_argument("--progress", action="store_true", help="Show curl-like download progress bar")

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
TRIGGER_NAMES = {
    VOD_trigger.PERSON: "person",
    VOD_trigger.VEHICLE: "vehicle",
    VOD_trigger.PET: "pet",
    VOD_trigger.MOTION: "motion",
}


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
    # Strip directory path and extension
    basename = filename.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    parts = basename.split("_")

    # Find the hex flags field — it's the second-to-last underscore-separated part
    # Old: RecM02_20230515_071811_071835_6D28900_13CE8C7
    # New: RecM07_20260220_000000_000024_0_6D28808000_E386CE
    if len(parts) < 6:
        return VOD_trigger.NONE

    hex_field = parts[-2]

    # Extract the 3 trigger nibbles: they start at offset 4 in the hex field
    # (first 4 chars like '6D28' are camera model prefix)
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


def print_progress(downloaded_bytes: int, total_bytes: int, filename: str):
    """Print a curl-like progress bar to stderr."""
    if total_bytes <= 0:
        return
    pct = downloaded_bytes / total_bytes * 100
    bar_width = 30
    filled = int(bar_width * downloaded_bytes / total_bytes)
    bar = "#" * filled + "-" * (bar_width - filled)
    dl_mb = downloaded_bytes / (1024 * 1024)
    total_mb = total_bytes / (1024 * 1024)
    sys.stderr.write(f"\r  [{bar}] {pct:5.1f}% {dl_mb:.1f}/{total_mb:.1f} MB  {filename}")
    sys.stderr.flush()
    if downloaded_bytes >= total_bytes:
        sys.stderr.write("\n")


async def run(
    *,
    config: dict,
    start: datetime,
    end: datetime,
    trigger_filter: VOD_trigger | None,
    latest: int | None,
    output_dir: Path,
    dry_run: bool,
    stream: str,
    verbose: bool = False,
    progress: bool = False,
):
    """Connect to camera, search, filter, and download recordings."""
    host = Host(
        config["host"],
        config["user"],
        config["password"],
        use_https=False,
        timeout=60,
    )

    try:
        print(f"Connecting to {config['host']}...")
        await host.get_host_data()
        print(f"Connected. Searching recordings from {start} to {end}...")

        _statuses, vods = await host.request_vod_files(
            channel=0,
            start=start,
            end=end,
            stream=stream,
            status_only=False,
        )

        print(f"Found {len(vods)} total recordings.")

        # Client-side filtering by trigger type
        filtered = filter_vods(vods, trigger_filter)
        trigger_desc = "all types"
        if trigger_filter is not None:
            names = [n for t, n in TRIGGER_NAMES.items() if trigger_filter & t]
            trigger_desc = ", ".join(names)

        print(f"Matched {len(filtered)} recordings for: {trigger_desc}")

        if not filtered:
            print("No matching recordings found.")
            return

        # Apply --latest limit
        filtered = apply_latest(filtered, latest)
        if latest:
            print(f"Limited to {len(filtered)} most recent.")

        if dry_run:
            print("\n--- Dry run: files that would be downloaded ---")
            for vod in filtered:
                trigger_name = get_primary_trigger_name(get_vod_triggers(vod))
                duration = int(vod.duration.total_seconds())
                line = f"  [{trigger_name}] {vod.start_time} - {vod.end_time} ({duration}s)"
                if verbose:
                    line += f" {vod.file_name}"
                print(line)
            print(f"\nTotal: {len(filtered)} files")
            return

        # Download files
        downloaded = 0
        failed = 0

        for i, vod in enumerate(filtered, 1):
            date_dir = vod.start_time.strftime("%Y-%m-%d")
            dest_dir = output_dir / date_dir
            dest_dir.mkdir(parents=True, exist_ok=True)

            filename = make_output_filename(vod)
            dest_path = dest_dir / filename

            if dest_path.exists():
                print(f"  [{i}/{len(filtered)}] Skipping (exists): {dest_path}")
                downloaded += 1
                continue

            if verbose:
                triggers = get_vod_triggers(vod)
                print(f"  [{i}/{len(filtered)}] {filename} triggers={triggers} src={vod.file_name}")
            else:
                print(f"  [{i}/{len(filtered)}] Downloading: {filename}...")

            try:
                dl = await host.download_vod(filename=vod.file_name)
                try:
                    total = dl.length
                    received = 0
                    with open(dest_path, "wb") as f:
                        async for chunk in dl.stream.iter_chunked(65536):
                            f.write(chunk)
                            received += len(chunk)
                            if progress:
                                print_progress(received, total, filename)
                    downloaded += 1
                    size_mb = dest_path.stat().st_size / (1024 * 1024)
                    print(f"           Saved: {dest_path} ({size_mb:.1f} MB)")
                finally:
                    dl.close()
            except Exception as e:
                failed += 1
                print(f"           FAILED: {e}")
                if dest_path.exists():
                    dest_path.unlink()

        print(f"\nDone. Downloaded: {downloaded}, Failed: {failed}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await host.logout()


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
        verbose=args.verbose,
        progress=args.progress,
    ))


if __name__ == "__main__":
    main()
