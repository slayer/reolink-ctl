"""Detection controls: motion, AI sensitivity/delay, PIR."""

from __future__ import annotations

from reolink_ctl.connection import connect, run_async
from reolink_ctl.output import print_result, print_error, print_success


# -- Motion ------------------------------------------------------------------

def _register_motion(detect_sub) -> None:
    parser = detect_sub.add_parser("motion", help="Motion detection control")
    motion_sub = parser.add_subparsers(dest="motion_command")

    # on / off / status as direct subcommands
    on_p = motion_sub.add_parser("on", help="Enable motion detection")
    on_p.set_defaults(func=_run_motion_on)

    off_p = motion_sub.add_parser("off", help="Disable motion detection")
    off_p.set_defaults(func=_run_motion_off)

    status_p = motion_sub.add_parser("status", help="Show motion detection status")
    status_p.set_defaults(func=_run_motion_status)

    # sensitivity as a nested subcommand
    sens_p = motion_sub.add_parser("sensitivity", help="Set motion sensitivity")
    sens_p.add_argument("value", type=int, help="Sensitivity (1-50)")
    sens_p.set_defaults(func=_run_motion_sensitivity)

    # Fallback when only `detect motion` is typed
    parser.set_defaults(func=_run_motion_status)


def _run_motion_on(args, config) -> None:
    run_async(_motion_on(args, config))


async def _motion_on(args, config) -> None:
    ch = config["channel"]
    async with connect(config) as host:
        await host.set_motion_detection(ch, True)
        print_success("Motion detection enabled", json_mode=args.json)


def _run_motion_off(args, config) -> None:
    run_async(_motion_off(args, config))


async def _motion_off(args, config) -> None:
    ch = config["channel"]
    async with connect(config) as host:
        await host.set_motion_detection(ch, False)
        print_success("Motion detection disabled", json_mode=args.json)


def _run_motion_status(args, config) -> None:
    run_async(_motion_status(args, config))


async def _motion_status(args, config) -> None:
    ch = config["channel"]
    async with connect(config) as host:
        data = {
            "motion_detected": host.motion_detected(ch),
            "sensitivity": host.md_sensitivity(ch),
        }
        print_result(data, json_mode=args.json)


def _run_motion_sensitivity(args, config) -> None:
    run_async(_motion_sensitivity(args, config))


async def _motion_sensitivity(args, config) -> None:
    ch = config["channel"]
    async with connect(config) as host:
        await host.set_md_sensitivity(ch, args.value)
        print_success(f"Motion sensitivity set to {args.value}", json_mode=args.json)


# -- AI ---------------------------------------------------------------------

def _register_ai(detect_sub) -> None:
    parser = detect_sub.add_parser("ai", help="AI detection settings")
    ai_sub = parser.add_subparsers(dest="ai_command")

    sens_p = ai_sub.add_parser("sensitivity", help="Set AI sensitivity")
    sens_p.add_argument("value", type=int, help="Sensitivity value")
    sens_p.add_argument("--type", required=True, dest="ai_type",
                        help="AI type (e.g. people, vehicle, dog_cat)")
    sens_p.set_defaults(func=_run_ai_sensitivity)

    delay_p = ai_sub.add_parser("delay", help="Set AI delay")
    delay_p.add_argument("value", type=int, help="Delay value")
    delay_p.add_argument("--type", required=True, dest="ai_type",
                         help="AI type (e.g. people, vehicle, dog_cat)")
    delay_p.set_defaults(func=_run_ai_delay)

    parser.set_defaults(func=_run_ai_help)


def _run_ai_help(args, config) -> None:
    print_error("Specify a subcommand: sensitivity, delay", json_mode=args.json)


def _run_ai_sensitivity(args, config) -> None:
    run_async(_ai_sensitivity(args, config))


async def _ai_sensitivity(args, config) -> None:
    ch = config["channel"]
    async with connect(config) as host:
        await host.set_ai_sensitivity(ch, args.value, ai_type=args.ai_type)
        print_success(
            f"AI sensitivity for {args.ai_type} set to {args.value}",
            json_mode=args.json,
        )


def _run_ai_delay(args, config) -> None:
    run_async(_ai_delay(args, config))


async def _ai_delay(args, config) -> None:
    ch = config["channel"]
    async with connect(config) as host:
        await host.set_ai_delay(ch, args.value, ai_type=args.ai_type)
        print_success(
            f"AI delay for {args.ai_type} set to {args.value}",
            json_mode=args.json,
        )


# -- PIR ---------------------------------------------------------------------

def _register_pir(detect_sub) -> None:
    parser = detect_sub.add_parser("pir", help="PIR sensor control")
    parser.add_argument("action", choices=["on", "off", "status"])
    parser.set_defaults(func=_run_pir_wrapper)


def _run_pir_wrapper(args, config) -> None:
    run_async(_run_pir(args, config))


async def _run_pir(args, config) -> None:
    ch = config["channel"]
    async with connect(config) as host:
        if args.action == "on":
            await host.set_pir(ch, enable=True)
            print_success("PIR sensor enabled", json_mode=args.json)
        elif args.action == "off":
            await host.set_pir(ch, enable=False)
            print_success("PIR sensor disabled", json_mode=args.json)
        else:
            data = {
                "pir_enabled": host.pir_enabled(ch),
                "pir_sensitivity": host.pir_sensitivity(ch),
            }
            print_result(data, json_mode=args.json)


# -- Top-level registration --------------------------------------------------

def register(subparsers) -> None:
    parser = subparsers.add_parser("detect", help="Detection controls")
    parser.set_defaults(func=run)
    detect_sub = parser.add_subparsers(dest="detect_command")

    _register_motion(detect_sub)
    _register_ai(detect_sub)
    _register_pir(detect_sub)


def run(args, config) -> None:
    # No sub-subcommand — show basic detection status
    run_async(_run(args, config))


async def _run(args, config) -> None:
    """Fallback: show motion and PIR status summary."""
    ch = config["channel"]
    async with connect(config) as host:
        data = {
            "motion_detected": host.motion_detected(ch),
            "motion_sensitivity": host.md_sensitivity(ch),
            "pir_enabled": host.pir_enabled(ch),
        }
        print_result(data, json_mode=args.json)
