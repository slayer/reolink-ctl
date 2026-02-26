"""PTZ control: movement, zoom, focus, presets, patrol, guard, tracking."""

from __future__ import annotations

from reolink_ctl.connection import connect, run_async
from reolink_ctl.output import print_result, print_error, print_success

DIRECTIONS = ["left", "right", "up", "down"]
TRACK_METHODS = {"digital": 2, "digitalfirst": 3, "pantiltfirst": 4}


def register(subparsers) -> None:
    parser = subparsers.add_parser("ptz", help="PTZ camera control")
    ptz_sub = parser.add_subparsers(dest="ptz_command", help="PTZ subcommands")

    # ptz move
    p_move = ptz_sub.add_parser("move", help="Move camera in a direction")
    p_move.add_argument("direction", choices=DIRECTIONS, help="Direction to move")
    p_move.add_argument("--speed", type=int, default=25, help="Movement speed (default: 25)")

    # ptz stop
    ptz_sub.add_parser("stop", help="Stop PTZ movement")

    # ptz zoom
    p_zoom = ptz_sub.add_parser("zoom", help="Zoom control")
    zoom_sub = p_zoom.add_subparsers(dest="zoom_action", help="Zoom action")
    zoom_sub.add_parser("in", help="Zoom in")
    zoom_sub.add_parser("out", help="Zoom out")
    p_zoom_set = zoom_sub.add_parser("set", help="Set zoom to absolute value")
    p_zoom_set.add_argument("value", type=int, help="Zoom level")

    # ptz focus
    p_focus = ptz_sub.add_parser("focus", help="Focus control")
    focus_sub = p_focus.add_subparsers(dest="focus_action", help="Focus action")
    p_focus_set = focus_sub.add_parser("set", help="Set focus to absolute value")
    p_focus_set.add_argument("value", type=int, help="Focus level")
    p_focus_auto = focus_sub.add_parser("auto", help="Toggle autofocus")
    p_focus_auto.add_argument("toggle", choices=["on", "off"], help="Enable or disable autofocus")

    # ptz preset
    p_preset = ptz_sub.add_parser("preset", help="Manage PTZ presets")
    preset_sub = p_preset.add_subparsers(dest="preset_action", help="Preset action")
    preset_sub.add_parser("list", help="List saved presets")
    p_preset_goto = preset_sub.add_parser("goto", help="Go to preset by ID")
    p_preset_goto.add_argument("id", type=int, help="Preset ID")

    # ptz patrol
    p_patrol = ptz_sub.add_parser("patrol", help="Patrol control")
    patrol_sub = p_patrol.add_subparsers(dest="patrol_action", help="Patrol action")
    patrol_sub.add_parser("start", help="Start patrol")
    patrol_sub.add_parser("stop", help="Stop patrol")
    patrol_sub.add_parser("list", help="List patrol configurations")

    # ptz guard
    p_guard = ptz_sub.add_parser("guard", help="Guard position control")
    guard_sub = p_guard.add_subparsers(dest="guard_action", help="Guard action")
    for name, hlp in [("on", "Enable guard"), ("off", "Disable guard"),
                       ("set", "Set current position as guard"), ("goto", "Go to guard position")]:
        gp = guard_sub.add_parser(name, help=hlp)
        gp.add_argument("--time", type=int, default=None, help="Guard return time in seconds")

    # ptz calibrate
    ptz_sub.add_parser("calibrate", help="Calibrate PTZ motor")

    # ptz track
    p_track = ptz_sub.add_parser("track", help="Auto-tracking control")
    track_sub = p_track.add_subparsers(dest="track_action", help="Tracking action")
    p_track_on = track_sub.add_parser("on", help="Enable auto-tracking")
    p_track_on.add_argument(
        "--method", choices=list(TRACK_METHODS.keys()),
        default="digital", help="Tracking method (default: digital)",
    )
    track_sub.add_parser("off", help="Disable auto-tracking")
    p_track_limit = track_sub.add_parser("limit", help="Set auto-tracking pan limits")
    p_track_limit.add_argument("--left", type=int, default=None, help="Left limit")
    p_track_limit.add_argument("--right", type=int, default=None, help="Right limit")

    # ptz position
    ptz_sub.add_parser("position", help="Show current pan position")

    parser.set_defaults(func=run)


def run(args, config) -> None:
    run_async(_run(args, config))


async def _run(args, config) -> None:
    ch = config["channel"]
    cmd = getattr(args, "ptz_command", None)

    if not cmd:
        print_error("No PTZ subcommand given. Use --help for usage.", json_mode=args.json)
        return

    async with connect(config) as host:
        if cmd == "move":
            await host.set_ptz_command(ch, command=args.direction.capitalize(), speed=args.speed)
            print_success(f"Moving {args.direction} (speed {args.speed})", json_mode=args.json)

        elif cmd == "stop":
            await host.set_ptz_command(ch, command="Stop")
            print_success("PTZ stopped", json_mode=args.json)

        elif cmd == "zoom":
            action = getattr(args, "zoom_action", None)
            if action == "in":
                await host.set_ptz_command(ch, command="ZoomInc")
                print_success("Zooming in", json_mode=args.json)
            elif action == "out":
                await host.set_ptz_command(ch, command="ZoomDec")
                print_success("Zooming out", json_mode=args.json)
            elif action == "set":
                await host.set_zoom(ch, args.value)
                print_success(f"Zoom set to {args.value}", json_mode=args.json)
            else:
                print_error("Zoom action required: in, out, or set", json_mode=args.json)

        elif cmd == "focus":
            action = getattr(args, "focus_action", None)
            if action == "set":
                await host.set_focus(ch, args.value)
                print_success(f"Focus set to {args.value}", json_mode=args.json)
            elif action == "auto":
                enabled = args.toggle == "on"
                await host.set_autofocus(ch, enabled)
                state = "enabled" if enabled else "disabled"
                print_success(f"Autofocus {state}", json_mode=args.json)
            else:
                print_error("Focus action required: set or auto", json_mode=args.json)

        elif cmd == "preset":
            action = getattr(args, "preset_action", None)
            if action == "list":
                presets = host.ptz_presets(ch)
                print_result(presets, json_mode=args.json)
            elif action == "goto":
                await host.set_ptz_command(ch, preset=args.id)
                print_success(f"Moving to preset {args.id}", json_mode=args.json)
            else:
                print_error("Preset action required: list or goto", json_mode=args.json)

        elif cmd == "patrol":
            action = getattr(args, "patrol_action", None)
            if action == "start":
                await host.ctrl_ptz_patrol(ch, True)
                print_success("Patrol started", json_mode=args.json)
            elif action == "stop":
                await host.ctrl_ptz_patrol(ch, False)
                print_success("Patrol stopped", json_mode=args.json)
            elif action == "list":
                patrols = host.ptz_patrols(ch)
                print_result(patrols, json_mode=args.json)
            else:
                print_error("Patrol action required: start, stop, or list", json_mode=args.json)

        elif cmd == "guard":
            action = getattr(args, "guard_action", None)
            # Build kwargs, only include time if explicitly provided
            kwargs = {}
            guard_time = getattr(args, "time", None)
            if guard_time is not None:
                kwargs["time"] = guard_time

            if action == "on":
                await host.set_ptz_guard(ch, enable=True, **kwargs)
                print_success("Guard enabled", json_mode=args.json)
            elif action == "off":
                await host.set_ptz_guard(ch, enable=False, **kwargs)
                print_success("Guard disabled", json_mode=args.json)
            elif action == "set":
                await host.set_ptz_guard(ch, command="setPos", **kwargs)
                print_success("Guard position set", json_mode=args.json)
            elif action == "goto":
                await host.set_ptz_guard(ch, command="toPos", **kwargs)
                print_success("Moving to guard position", json_mode=args.json)
            else:
                print_error("Guard action required: on, off, set, or goto", json_mode=args.json)

        elif cmd == "calibrate":
            await host.ptz_callibrate(ch)
            print_success("PTZ calibration started", json_mode=args.json)

        elif cmd == "track":
            action = getattr(args, "track_action", None)
            if action == "on":
                method = TRACK_METHODS[args.method]
                await host.set_auto_tracking(ch, enable=True, method=method)
                print_success(f"Auto-tracking enabled (method: {args.method})", json_mode=args.json)
            elif action == "off":
                await host.set_auto_tracking(ch, enable=False)
                print_success("Auto-tracking disabled", json_mode=args.json)
            elif action == "limit":
                kwargs = {}
                if args.left is not None:
                    kwargs["left"] = args.left
                if args.right is not None:
                    kwargs["right"] = args.right
                if not kwargs:
                    print_error("At least one of --left or --right required", json_mode=args.json)
                    return
                await host.set_auto_track_limit(ch, **kwargs)
                print_success(f"Track limits set: {kwargs}", json_mode=args.json)
            else:
                print_error("Track action required: on, off, or limit", json_mode=args.json)

        elif cmd == "position":
            pos = host.ptz_pan_position(ch)
            print_result({"pan_position": pos}, json_mode=args.json)
