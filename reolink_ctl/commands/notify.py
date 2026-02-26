"""Notification controls: push, email, FTP, recording, buzzer."""

from __future__ import annotations

from reolink_ctl.connection import connect, run_async
from reolink_ctl.output import print_result, print_error, print_success

NOTIFY_TYPES = ("push", "email", "ftp", "recording", "buzzer")

# Maps type name to (setter, getter) — setter takes (ch, bool), getter takes (ch)
_API_MAP = {
    "push":      ("set_push",      "push_enabled"),
    "email":     ("set_email",     "email_enabled"),
    "ftp":       ("set_ftp",       "ftp_enabled"),
    "recording": ("set_recording", "recording_enabled"),
    "buzzer":    ("set_buzzer",    "buzzer_enabled"),
}


def register(subparsers) -> None:
    parser = subparsers.add_parser("notify", help="Notification settings")
    parser.add_argument("type", choices=NOTIFY_TYPES, help="Notification type")
    parser.add_argument("action", choices=["on", "off", "status"], help="Enable, disable, or check status")
    parser.set_defaults(func=run)


def run(args, config) -> None:
    run_async(_run(args, config))


async def _run(args, config) -> None:
    channel = config["channel"]
    ntype = args.type
    setter_name, getter_name = _API_MAP[ntype]

    async with connect(config) as host:
        if args.action == "status":
            getter = getattr(host, getter_name)
            enabled = getter(channel)
            print_result({ntype: enabled}, json_mode=args.json)
        else:
            enable = args.action == "on"
            setter = getattr(host, setter_name)
            await setter(channel, enable)
            state = "enabled" if enable else "disabled"
            print_success(f"{ntype.capitalize()} {state}", json_mode=args.json)
