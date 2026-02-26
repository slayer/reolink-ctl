"""Show RTSP/RTMP/FLV stream URLs for a camera channel."""

from __future__ import annotations

from reolink_ctl.connection import connect, run_async
from reolink_ctl.output import print_result, print_error


FORMATS = ("rtsp", "rtmp", "flv")


def register(subparsers) -> None:
    parser = subparsers.add_parser("stream", help="Show stream URLs")
    parser.add_argument(
        "-f", "--format", choices=FORMATS, default=None,
        help="Stream format (default: show all)",
    )
    parser.add_argument(
        "-s", "--stream", choices=["main", "sub"], default="main",
        help="Stream type (default: main)",
    )
    parser.set_defaults(func=run)


def run(args, config) -> None:
    run_async(_run(args, config))


async def _run(args, config) -> None:
    channel = config["channel"]
    stream = args.stream
    # Which formats to show — single or all
    formats = [args.format] if args.format else list(FORMATS)

    async with connect(config) as host:
        urls = {}
        for fmt in formats:
            if fmt == "rtsp":
                url = await host.get_rtsp_stream_source(channel, stream=stream)
            elif fmt == "rtmp":
                url = host.get_rtmp_stream_source(channel, stream=stream)
            elif fmt == "flv":
                url = host.get_flv_stream_source(channel, stream=stream)
            else:
                continue
            urls[fmt] = url

        # Drop None values so the user sees only working URLs
        available = {k: v for k, v in urls.items() if v is not None}

        if not available:
            print_error("No stream URLs available", json_mode=args.json)
            return

        print_result(available, json_mode=args.json)
