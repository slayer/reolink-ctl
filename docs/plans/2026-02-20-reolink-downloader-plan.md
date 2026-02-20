# Reolink Video Downloader Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Python CLI tool to download Reolink camera recordings filtered by AI detection type (person, vehicle, animal, etc.)

**Architecture:** Single-file CLI script using `reolink_aio` for camera communication, `argparse` for CLI parsing, `python-dotenv` for config. Async Python with `asyncio.run()` entry point.

**Tech Stack:** Python 3.11+, reolink_aio, python-dotenv, aiohttp (transitive)

---

### Task 1: Project setup

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "reolink-downloader"
version = "0.1.0"
description = "Download Reolink camera recordings filtered by AI detection type"
requires-python = ">=3.11"
dependencies = [
    "reolink_aio",
    "python-dotenv",
]

[project.scripts]
reolink-download = "download:main"
```

**Step 2: Create .gitignore**

```
.env
downloads/
__pycache__/
*.pyc
.venv/
```

**Step 3: Create .env.example**

```
REOLINK_HOST=<camera-ip>
REOLINK_USER=admin
REOLINK_PASSWORD=
```

**Step 4: Install dependencies**

Run: `python -m venv .venv && source .venv/bin/activate && pip install reolink_aio python-dotenv`

**Step 5: Commit**

```bash
git add pyproject.toml .gitignore .env.example
git commit -m "Setup project structure and dependencies"
```

---

### Task 2: CLI argument parsing

**Files:**
- Create: `download.py`
- Create: `tests/test_cli.py`

**Step 1: Write tests for argument parsing**

```python
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
    trigger = build_trigger_filter(person=True, vehicle=False, animal=False,
                                    face=False, doorbell=False, motion=False, all_triggers=False)
    assert trigger & VOD_trigger.PERSON


def test_build_trigger_filter_combined():
    from download import build_trigger_filter
    from reolink_aio.typings import VOD_trigger
    trigger = build_trigger_filter(person=True, vehicle=True, animal=False,
                                    face=False, doorbell=False, motion=False, all_triggers=False)
    assert trigger & VOD_trigger.PERSON
    assert trigger & VOD_trigger.VEHICLE


def test_build_trigger_filter_all_returns_none():
    from download import build_trigger_filter
    trigger = build_trigger_filter(person=False, vehicle=False, animal=False,
                                    face=False, doorbell=False, motion=False, all_triggers=True)
    assert trigger is None


def test_build_trigger_filter_none_selected_returns_none():
    """No flags selected = no filter = return all."""
    from download import build_trigger_filter
    trigger = build_trigger_filter(person=False, vehicle=False, animal=False,
                                    face=False, doorbell=False, motion=False, all_triggers=False)
    assert trigger is None
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/vlad/dev/my/reolink && source .venv/bin/activate && python -m pytest tests/test_cli.py -v`
Expected: FAIL — `download.py` doesn't exist yet.

**Step 3: Implement CLI parsing and helper functions**

```python
# download.py
"""Download Reolink camera recordings filtered by AI detection type."""

import argparse
import asyncio
import os
import re
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

from dotenv import load_dotenv
from reolink_aio.typings import VOD_trigger


def parse_since(since_str: str) -> tuple[datetime, datetime]:
    """Parse relative time like '30m', '2h', '3d' into (start, end) datetimes."""
    match = re.fullmatch(r"(\d+)([mhd])", since_str)
    if not match:
        raise ValueError(f"Invalid --since format: {since_str!r}. Use e.g. 30m, 2h, 3d")

    amount = int(match.group(1))
    unit = match.group(2)
    multiplier = {"m": 60, "h": 3600, "d": 86400}[unit]

    end = datetime.now()
    start = end - timedelta(seconds=amount * multiplier)
    return start, end


def parse_date_range(
    date_str: str | None,
    from_str: str | None,
    to_str: str | None,
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
    animal: bool,
    face: bool,
    doorbell: bool,
    motion: bool,
    all_triggers: bool,
) -> VOD_trigger | None:
    """Build a VOD_trigger filter from CLI flags. Returns None if no filter (= all)."""
    if all_triggers:
        return None

    trigger = VOD_trigger.NONE
    if person:
        trigger |= VOD_trigger.PERSON
    if vehicle:
        trigger |= VOD_trigger.VEHICLE
    if animal:
        trigger |= VOD_trigger.ANIMAL
    if face:
        trigger |= VOD_trigger.FACE
    if doorbell:
        trigger |= VOD_trigger.DOORBELL
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

    # Trigger filters
    triggers = parser.add_argument_group("trigger filters")
    triggers.add_argument("--person", action="store_true", help="Person detection")
    triggers.add_argument("--vehicle", action="store_true", help="Vehicle detection")
    triggers.add_argument("--animal", action="store_true", help="Animal/pet detection")
    triggers.add_argument("--face", action="store_true", help="Face detection")
    triggers.add_argument("--doorbell", action="store_true", help="Doorbell press")
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


def main():
    parser = build_parser()
    args = parser.parse_args()
    config = resolve_config(args)

    if not config["host"]:
        parser.error("Camera host required: use --host or set REOLINK_HOST in .env")
    if not config["password"]:
        parser.error("Password required: use --password or set REOLINK_PASSWORD in .env")

    # Determine time range
    if args.since:
        start, end = parse_since(args.since)
    else:
        start, end = parse_date_range(args.date, args.from_date, args.to_date)

    trigger_filter = build_trigger_filter(
        person=args.person,
        vehicle=args.vehicle,
        animal=args.animal,
        face=args.face,
        doorbell=args.doorbell,
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
```

Note: The `run()` async function is a stub for now — implemented in Task 3.

**Step 4: Run tests to verify they pass**

Run: `cd /Users/vlad/dev/my/reolink && source .venv/bin/activate && python -m pytest tests/test_cli.py -v`
Expected: All PASS.

**Step 5: Commit**

```bash
git add download.py tests/test_cli.py
git commit -m "Add CLI argument parsing with time, trigger, and connection flags"
```

---

### Task 3: Camera connection and file search

**Files:**
- Modify: `download.py` — add `run()` async function
- Create: `tests/test_download.py`

**Step 1: Write tests for file filtering and filename generation**

```python
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
        make_mock_vod(12, 0, 12, 5, VOD_trigger.ANIMAL),
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
    # Primary trigger in name
    assert name.endswith(".mp4")
    assert "103000" in name
    assert "104500" in name


def test_make_output_filename_motion():
    from download import make_output_filename
    vod = make_mock_vod(14, 0, 14, 10, VOD_trigger.MOTION)
    name = make_output_filename(vod)
    assert name == "motion_140000_141000.mp4"
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/vlad/dev/my/reolink && source .venv/bin/activate && python -m pytest tests/test_download.py -v`
Expected: FAIL — `filter_vods`, `apply_latest`, `make_output_filename` not defined.

**Step 3: Implement filtering and filename helpers in download.py**

Add these functions to `download.py` (before `main()`):

```python
# -- Trigger name mapping for filenames --
TRIGGER_NAMES = {
    VOD_trigger.PERSON: "person",
    VOD_trigger.VEHICLE: "vehicle",
    VOD_trigger.ANIMAL: "animal",
    VOD_trigger.FACE: "face",
    VOD_trigger.DOORBELL: "doorbell",
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
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/vlad/dev/my/reolink && source .venv/bin/activate && python -m pytest tests/test_download.py -v`
Expected: All PASS.

**Step 5: Commit**

```bash
git add download.py tests/test_download.py
git commit -m "Add VOD filtering, latest limit, and output filename generation"
```

---

### Task 4: Download logic (the `run()` function)

**Files:**
- Modify: `download.py` — implement the `run()` async function

**Step 1: Implement the `run()` function**

Add to `download.py`:

```python
from reolink_aio.api import Host


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
                trigger_name = get_primary_trigger_name(vod.triggers)
                duration = int(vod.duration.total_seconds())
                print(f"  [{trigger_name}] {vod.start_time} - {vod.end_time} ({duration}s) {vod.file_name}")
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

            print(f"  [{i}/{len(filtered)}] Downloading: {filename}...")

            try:
                dl = await host.download_vod(filename=vod.file_name)
                try:
                    with open(dest_path, "wb") as f:
                        async for chunk in dl.stream.iter_chunked(65536):
                            f.write(chunk)
                    downloaded += 1
                    size_mb = dest_path.stat().st_size / (1024 * 1024)
                    print(f"           Saved: {dest_path} ({size_mb:.1f} MB)")
                finally:
                    dl.close()
            except Exception as e:
                failed += 1
                print(f"           FAILED: {e}")
                # Clean up partial file
                if dest_path.exists():
                    dest_path.unlink()

        print(f"\nDone. Downloaded: {downloaded}, Failed: {failed}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await host.logout()
```

**Step 2: Verify the script runs with --help**

Run: `cd /Users/vlad/dev/my/reolink && source .venv/bin/activate && python download.py --help`
Expected: Shows help text with all argument groups.

**Step 3: Verify dry-run against actual camera**

Run: `cd /Users/vlad/dev/my/reolink && source .venv/bin/activate && python download.py -H <camera-ip> -u admin -p <password> --person --date today --dry-run`
Expected: Connects to camera, lists person detection recordings (or "No matching recordings found").

**Step 4: Commit**

```bash
git add download.py
git commit -m "Add camera connection, search, and download logic"
```

---

### Task 5: Run all tests and manual end-to-end test

**Step 1: Run full test suite**

Run: `cd /Users/vlad/dev/my/reolink && source .venv/bin/activate && python -m pytest tests/ -v`
Expected: All tests PASS.

**Step 2: Manual end-to-end test — dry run for person detection today**

Run: `cd /Users/vlad/dev/my/reolink && source .venv/bin/activate && python download.py -H <camera-ip> -u admin -p <password> --person --date today --dry-run`

**Step 3: Manual end-to-end test — download latest 2 person detection videos**

Run: `cd /Users/vlad/dev/my/reolink && source .venv/bin/activate && python download.py -H <camera-ip> -u admin -p <password> --person --latest 2`
Expected: Downloads 2 MP4 files to `./downloads/2026-02-20/`.

**Step 4: Verify downloaded files play correctly**

Run: `ls -la downloads/2026-02-20/ && file downloads/2026-02-20/*.mp4`
Expected: Files are valid MP4s.

**Step 5: Final commit**

```bash
git add -A
git commit -m "Complete Reolink video downloader with person detection filtering"
```
