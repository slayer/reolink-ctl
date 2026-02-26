"""Lighting controls: IR, spotlight, white LED, status LED."""

from __future__ import annotations

from reolink_ctl.connection import connect, run_async
from reolink_ctl.output import print_result, print_error, print_success


# -- IR ----------------------------------------------------------------------

def _register_ir(light_sub) -> None:
    parser = light_sub.add_parser("ir", help="Infrared light control")
    parser.add_argument("action", choices=["on", "off", "status"])
    parser.set_defaults(func=_run_ir_wrapper)


def _run_ir_wrapper(args, config) -> None:
    run_async(_run_ir(args, config))


async def _run_ir(args, config) -> None:
    ch = config["channel"]
    async with connect(config) as host:
        if args.action == "on":
            await host.set_ir_lights(ch, True)
            print_success("IR lights enabled", json_mode=args.json)
        elif args.action == "off":
            await host.set_ir_lights(ch, False)
            print_success("IR lights disabled", json_mode=args.json)
        else:
            enabled = host.ir_enabled(ch)
            print_result({"ir_enabled": enabled}, json_mode=args.json)


# -- Spotlight ---------------------------------------------------------------

def _register_spotlight(light_sub) -> None:
    parser = light_sub.add_parser("spotlight", help="Spotlight control")
    parser.add_argument("action", choices=["on", "off", "status"])
    parser.set_defaults(func=_run_spotlight_wrapper)


def _run_spotlight_wrapper(args, config) -> None:
    run_async(_run_spotlight(args, config))


async def _run_spotlight(args, config) -> None:
    ch = config["channel"]
    async with connect(config) as host:
        if args.action == "on":
            await host.set_spotlight(ch, True)
            print_success("Spotlight enabled", json_mode=args.json)
        elif args.action == "off":
            await host.set_spotlight(ch, False)
            print_success("Spotlight disabled", json_mode=args.json)
        else:
            # whiteled_state serves as proxy for spotlight status
            state = host.whiteled_state(ch)
            print_result({"spotlight_on": state}, json_mode=args.json)


# -- White LED ---------------------------------------------------------------

def _register_whiteled(light_sub) -> None:
    parser = light_sub.add_parser("whiteled", help="White LED settings")
    parser.add_argument("--state", choices=["on", "off"], default=None,
                        help="Turn white LED on or off")
    parser.add_argument("--brightness", type=int, default=None,
                        help="Brightness level")
    parser.add_argument("--mode", type=int, default=None,
                        help="White LED mode")
    parser.set_defaults(func=_run_whiteled_wrapper)


def _run_whiteled_wrapper(args, config) -> None:
    run_async(_run_whiteled(args, config))


async def _run_whiteled(args, config) -> None:
    ch = config["channel"]
    async with connect(config) as host:
        has_flags = (args.state is not None
                     or args.brightness is not None
                     or args.mode is not None)

        if has_flags:
            state_bool = None
            if args.state is not None:
                state_bool = args.state == "on"
            await host.set_whiteled(
                ch,
                state=state_bool,
                brightness=args.brightness,
                mode=args.mode,
            )
            print_success("White LED settings updated", json_mode=args.json)
        else:
            data = {
                "state": host.whiteled_state(ch),
                "mode": host.whiteled_mode(ch),
                "brightness": host.whiteled_brightness(ch),
            }
            print_result(data, json_mode=args.json)


# -- Status LED --------------------------------------------------------------

STATUS_LED_MODES = {
    "stayoff": "stayoff",
    "auto": "auto",
    "alwaysonatnight": "alwaysonatnight",
    "alwayson": "alwayson",
}


def _register_status_led(light_sub) -> None:
    parser = light_sub.add_parser("status-led", help="Status LED control")
    parser.add_argument(
        "mode_or_status",
        choices=["stayoff", "auto", "alwaysonatnight", "alwayson", "status"],
        help="LED mode to set, or 'status' to query",
    )
    parser.set_defaults(func=_run_status_led_wrapper)


def _run_status_led_wrapper(args, config) -> None:
    run_async(_run_status_led(args, config))


async def _run_status_led(args, config) -> None:
    ch = config["channel"]
    async with connect(config) as host:
        if args.mode_or_status == "status":
            enabled = host.status_led_enabled(ch)
            print_result({"status_led_enabled": enabled}, json_mode=args.json)
        else:
            mode_value = STATUS_LED_MODES[args.mode_or_status]
            await host.set_status_led(ch, mode_value)
            print_success(f"Status LED set to {mode_value}", json_mode=args.json)


# -- Top-level registration --------------------------------------------------

def register(subparsers) -> None:
    parser = subparsers.add_parser("light", help="Lighting controls")
    parser.set_defaults(func=run)
    light_sub = parser.add_subparsers(dest="light_command")

    _register_ir(light_sub)
    _register_spotlight(light_sub)
    _register_whiteled(light_sub)
    _register_status_led(light_sub)


def run(args, config) -> None:
    # Reached when no sub-subcommand given — show help
    run_async(_run(args, config))


async def _run(args, config) -> None:
    """Fallback: show all light-related status at once."""
    ch = config["channel"]
    async with connect(config) as host:
        data = {
            "ir_enabled": host.ir_enabled(ch),
            "whiteled_state": host.whiteled_state(ch),
            "whiteled_mode": host.whiteled_mode(ch),
            "whiteled_brightness": host.whiteled_brightness(ch),
            "status_led_enabled": host.status_led_enabled(ch),
        }
        print_result(data, json_mode=args.json)
