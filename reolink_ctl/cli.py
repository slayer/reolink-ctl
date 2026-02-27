"""Top-level CLI parser, global flags, and subcommand dispatch."""

from __future__ import annotations

import argparse
import sys

from reolink_ctl import __version__
from reolink_ctl.connection import resolve_config
from reolink_ctl.output import print_error

# All command modules — each exports register(subparsers) and run(args, config)
from reolink_ctl.commands import (
    info,
    snapshot,
    stream,
    download,
    ptz,
    light,
    image,
    detect,
    audio,
    notify,
    webhook,
    system,
    config,
)

COMMAND_MODULES = [
    info, snapshot, stream, download, ptz,
    light, image, detect, audio, notify, webhook, system, config,
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reolink-ctl",
        description="CLI for Reolink camera control.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # Global connection flags
    parser.add_argument("-H", "--host", help="Camera IP (env: REOLINK_HOST)")
    parser.add_argument("-u", "--user", help="Username (env: REOLINK_USER)")
    parser.add_argument("-p", "--password", help="Password (env: REOLINK_PASSWORD)")
    parser.add_argument("-c", "--channel", type=int, default=0, help="Camera channel (default: 0)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    for mod in COMMAND_MODULES:
        mod.register(subparsers)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    config = resolve_config(args)

    if not config["host"]:
        print_error("Camera host required: use --host or set REOLINK_HOST in .env", json_mode=args.json)
        sys.exit(1)
    if not config["password"]:
        print_error("Password required: use --password or set REOLINK_PASSWORD in .env", json_mode=args.json)
        sys.exit(1)

    # Each command module sets args.func = run
    args.func(args, config)
