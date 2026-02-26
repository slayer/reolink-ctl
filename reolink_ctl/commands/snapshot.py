"""Capture a JPEG snapshot from the camera."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reolink_ctl.connection import connect, run_async
from reolink_ctl.output import print_error, print_success


def register(subparsers) -> None:
    parser = subparsers.add_parser("snapshot", help="Capture a snapshot")
    parser.add_argument("-o", "--output", help="Output file path (default: snapshot_TIMESTAMP.jpg)")
    parser.add_argument(
        "-s", "--stream", choices=["main", "sub"], default="main",
        help="Stream type (default: main)",
    )
    parser.set_defaults(func=run)


def run(args, config) -> None:
    run_async(_run(args, config))


async def _run(args, config) -> None:
    channel = config["channel"]

    async with connect(config) as host:
        data = await host.get_snapshot(channel, stream=args.stream)

        if not data:
            print_error("Camera returned empty snapshot", json_mode=args.json)
            return

        if args.output:
            output = Path(args.output)
        else:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = Path(f"snapshot_{ts}.jpg")

        output.write_bytes(data)
        size_kb = len(data) / 1024
        print_success(f"Saved {output} ({size_kb:.1f} KB)", json_mode=args.json)
