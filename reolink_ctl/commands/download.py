"""Download VOD recordings from camera."""

from __future__ import annotations

import sys
from pathlib import Path

from reolink_ctl.connection import connect, run_async
from reolink_ctl.output import print_result, print_error, print_success
from reolink_ctl.time_utils import parse_since, parse_date_range
from reolink_ctl.vod import (
    build_trigger_filter,
    filter_vods,
    apply_latest,
    get_primary_trigger_name,
    get_vod_triggers,
    make_output_filename,
    TRIGGER_NAMES,
)


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


def register(subparsers):
    p = subparsers.add_parser("download", help="Download VOD recordings")

    # Trigger filters
    triggers = p.add_argument_group("trigger filters")
    triggers.add_argument("--person", action="store_true", help="Person detection")
    triggers.add_argument("--vehicle", "--car", action="store_true", help="Vehicle/car detection")
    triggers.add_argument("--pet", action="store_true", help="Pet/animal detection")
    triggers.add_argument("--motion", action="store_true", help="Motion detection")
    triggers.add_argument("--all", dest="all_triggers", action="store_true",
                          help="All trigger types (default if none selected)")

    # Time selection
    time = p.add_argument_group("time selection")
    time.add_argument("--date", dest="date", help="Specific date: YYYY-MM-DD, 'today', 'yesterday'")
    time.add_argument("--from", dest="from_date", help="Range start: YYYY-MM-DD")
    time.add_argument("--to", dest="to_date", help="Range end: YYYY-MM-DD")
    time.add_argument("--since", help="Relative period: 30m, 2h, 1d, 3d")
    time.add_argument("--latest", type=int, help="Limit to N most recent recordings")

    # Output
    output = p.add_argument_group("output")
    output.add_argument("--output-dir", default="./downloads", help="Download directory (default: ./downloads)")
    output.add_argument("--dry-run", action="store_true", help="List files without downloading")
    output.add_argument("--stream", choices=["main", "sub"], default="main", help="Stream quality (default: main)")
    output.add_argument("--high", dest="stream", action="store_const", const="main", help="High quality (alias for --stream main)")
    output.add_argument("--low", dest="stream", action="store_const", const="sub", help="Low quality (alias for --stream sub)")
    output.add_argument("--progress", action="store_true", help="Show download progress bar")

    p.set_defaults(func=run)


def run(args, config):
    # Validate time args
    if (args.from_date or args.to_date) and not (args.from_date and args.to_date):
        print_error("--from and --to must be used together", json_mode=args.json)
        sys.exit(1)
    if args.since and (args.date or args.from_date):
        print_error("--since cannot be combined with --date or --from/--to", json_mode=args.json)
        sys.exit(1)

    run_async(_run(args, config))


async def _run(args, config):
    ch = config["channel"]
    json_mode = args.json

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

    async with connect(config) as host:
        print(f"Searching recordings from {start} to {end}...")

        _statuses, vods = await host.request_vod_files(
            channel=ch,
            start=start,
            end=end,
            stream=args.stream,
            status_only=False,
        )

        print(f"Found {len(vods)} total recordings.")

        filtered = filter_vods(vods, trigger_filter)
        trigger_desc = "all types"
        if trigger_filter is not None:
            names = [n for t, n in TRIGGER_NAMES.items() if trigger_filter & t]
            trigger_desc = ", ".join(names)

        print(f"Matched {len(filtered)} recordings for: {trigger_desc}")

        if not filtered:
            print("No matching recordings found.")
            return

        filtered = apply_latest(filtered, args.latest)
        if args.latest:
            print(f"Limited to {len(filtered)} most recent.")

        if args.dry_run:
            print("\n--- Dry run: files that would be downloaded ---")
            for vod in filtered:
                trigger_name = get_primary_trigger_name(get_vod_triggers(vod))
                duration = int(vod.duration.total_seconds())
                line = f"  [{trigger_name}] {vod.start_time} - {vod.end_time} ({duration}s)"
                if args.verbose:
                    line += f" {vod.file_name}"
                print(line)
            print(f"\nTotal: {len(filtered)} files")
            return

        # Download files
        output_dir = Path(args.output_dir)
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

            if args.verbose:
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
                            if args.progress:
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
