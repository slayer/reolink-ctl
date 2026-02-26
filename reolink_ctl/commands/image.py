"""Image settings: brightness, contrast, saturation, day/night, HDR."""

from __future__ import annotations

from reolink_ctl.connection import connect, run_async
from reolink_ctl.output import print_result, print_error, print_success


# -- Get ---------------------------------------------------------------------

def _register_get(image_sub) -> None:
    parser = image_sub.add_parser("get", help="Show current image settings")
    parser.set_defaults(func=_run_get_wrapper)


def _run_get_wrapper(args, config) -> None:
    run_async(_run_get(args, config))


async def _run_get(args, config) -> None:
    ch = config["channel"]
    async with connect(config) as host:
        data = {
            "brightness": host.image_brightness(ch),
            "contrast": host.image_contrast(ch),
            "saturation": host.image_saturation(ch),
            "sharpness": host.image_sharpness(ch),
            "hue": host.image_hue(ch),
            "daynight": host.daynight_state(ch),
            "hdr": host.HDR_on(ch),
        }
        print_result(data, json_mode=args.json)


# -- Set ---------------------------------------------------------------------

def _register_set(image_sub) -> None:
    parser = image_sub.add_parser("set", help="Adjust image parameters")
    parser.add_argument("--bright", type=int, default=None, help="Brightness")
    parser.add_argument("--contrast", type=int, default=None, help="Contrast")
    parser.add_argument("--saturation", type=int, default=None, help="Saturation")
    parser.add_argument("--sharpness", type=int, default=None, help="Sharpness")
    parser.add_argument("--hue", type=int, default=None, help="Hue")
    parser.set_defaults(func=_run_set_wrapper)


def _run_set_wrapper(args, config) -> None:
    run_async(_run_set(args, config))


async def _run_set(args, config) -> None:
    ch = config["channel"]
    async with connect(config) as host:
        await host.set_image(
            ch,
            bright=args.bright,
            contrast=args.contrast,
            saturation=args.saturation,
            hue=args.hue,
            sharpen=args.sharpness,
        )
        print_success("Image settings updated", json_mode=args.json)


# -- Day/Night --------------------------------------------------------------

DAYNIGHT_MAP = {
    "auto": "Auto",
    "color": "Color",
    "blackwhite": "Black&White",
}


def _register_daynight(image_sub) -> None:
    parser = image_sub.add_parser("daynight", help="Set day/night mode")
    parser.add_argument("mode", choices=["auto", "color", "blackwhite"])
    parser.set_defaults(func=_run_daynight_wrapper)


def _run_daynight_wrapper(args, config) -> None:
    run_async(_run_daynight(args, config))


async def _run_daynight(args, config) -> None:
    ch = config["channel"]
    value = DAYNIGHT_MAP[args.mode]
    async with connect(config) as host:
        await host.set_daynight(ch, value)
        print_success(f"Day/night mode set to {value}", json_mode=args.json)


# -- HDR ---------------------------------------------------------------------

HDR_MAP = {
    "off": 0,
    "auto": 1,
    "on": 2,
}


def _register_hdr(image_sub) -> None:
    parser = image_sub.add_parser("hdr", help="Set HDR mode")
    parser.add_argument("mode", choices=["off", "auto", "on"])
    parser.set_defaults(func=_run_hdr_wrapper)


def _run_hdr_wrapper(args, config) -> None:
    run_async(_run_hdr(args, config))


async def _run_hdr(args, config) -> None:
    ch = config["channel"]
    value = HDR_MAP[args.mode]
    async with connect(config) as host:
        await host.set_HDR(ch, value)
        print_success(f"HDR set to {args.mode}", json_mode=args.json)


# -- Top-level registration --------------------------------------------------

def register(subparsers) -> None:
    parser = subparsers.add_parser("image", help="Image settings")
    parser.set_defaults(func=run)
    image_sub = parser.add_subparsers(dest="image_command")

    _register_get(image_sub)
    _register_set(image_sub)
    _register_daynight(image_sub)
    _register_hdr(image_sub)


def run(args, config) -> None:
    # No sub-subcommand — show current settings
    run_async(_run(args, config))


async def _run(args, config) -> None:
    """Fallback: same as 'image get'."""
    await _run_get(args, config)
