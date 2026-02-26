"""System commands: reboot, firmware, time, NTP, OSD, network ports."""

from __future__ import annotations

from reolink_ctl.connection import connect, run_async
from reolink_ctl.output import print_result, print_error, print_success


def _parse_on_off(value: str | None) -> bool | None:
    """Convert 'on'/'off' string to bool, or None if absent."""
    if value is None:
        return None
    return value == "on"


def register(subparsers) -> None:
    parser = subparsers.add_parser("system", help="System administration")
    system_command = parser.add_subparsers(dest="system_command")
    system_command.required = True

    # system reboot
    reboot = system_command.add_parser("reboot", help="Reboot the device")
    reboot.set_defaults(func=run)

    # system firmware <check|update|progress>
    fw = system_command.add_parser("firmware", help="Firmware management")
    fw.add_argument("action", choices=["check", "update", "progress"])
    fw.set_defaults(func=run)

    # system time <get|set> [--tz-offset N]
    time_p = system_command.add_parser("time", help="Time settings")
    time_p.add_argument("action", choices=["get", "set"])
    time_p.add_argument("--tz-offset", type=int, default=None, help="Timezone offset")
    time_p.set_defaults(func=run)

    # system ntp <set|sync> [--server S] [--port N]
    ntp = system_command.add_parser("ntp", help="NTP settings")
    ntp.add_argument("action", choices=["set", "sync"])
    ntp.add_argument("--server", default=None, help="NTP server address")
    ntp.add_argument("--port", type=int, default=None, help="NTP server port")
    ntp.set_defaults(func=run)

    # system osd set [--name-pos POS] [--date-pos POS] [--watermark on|off]
    osd = system_command.add_parser("osd", help="OSD (on-screen display) settings")
    osd.add_argument("action", choices=["set"])
    osd.add_argument("--name-pos", default=None, help="Camera name position")
    osd.add_argument("--date-pos", default=None, help="Date/time position")
    osd.add_argument("--watermark", choices=["on", "off"], default=None, help="Watermark on/off")
    osd.set_defaults(func=run)

    # system ports set [--onvif on|off] [--rtmp on|off] [--rtsp on|off]
    ports = system_command.add_parser("ports", help="Network port settings")
    ports.add_argument("action", choices=["set"])
    ports.add_argument("--onvif", choices=["on", "off"], default=None, help="ONVIF on/off")
    ports.add_argument("--rtmp", choices=["on", "off"], default=None, help="RTMP on/off")
    ports.add_argument("--rtsp", choices=["on", "off"], default=None, help="RTSP on/off")
    ports.set_defaults(func=run)


def run(args, config) -> None:
    run_async(_run(args, config))


async def _run(args, config) -> None:
    channel = config["channel"]
    cmd = args.system_command

    async with connect(config) as host:
        if cmd == "reboot":
            await host.reboot()
            print_success("Reboot initiated", json_mode=args.json)

        elif cmd == "firmware":
            if args.action == "check":
                result = await host.check_new_firmware()
                print_result(result, json_mode=args.json)
            elif args.action == "update":
                await host.update_firmware()
                print_success("Firmware update started", json_mode=args.json)
            else:
                result = await host.update_progress()
                print_result(result, json_mode=args.json)

        elif cmd == "time":
            if args.action == "get":
                result = await host.async_get_time()
                print_result(result, json_mode=args.json)
            else:
                if args.tz_offset is None:
                    print_error("--tz-offset is required for 'set'", json_mode=args.json)
                    return
                await host.set_time(tzOffset=args.tz_offset)
                print_success(f"Time zone offset set to {args.tz_offset}", json_mode=args.json)

        elif cmd == "ntp":
            if args.action == "set":
                kwargs = {"enable": True}
                if args.server is not None:
                    kwargs["server"] = args.server
                if args.port is not None:
                    kwargs["port"] = args.port
                await host.set_ntp(**kwargs)
                print_success("NTP configured", json_mode=args.json)
            else:
                await host.sync_ntp()
                print_success("NTP sync requested", json_mode=args.json)

        elif cmd == "osd":
            watermark_bool = _parse_on_off(args.watermark)
            await host.set_osd(
                channel,
                namePos=args.name_pos,
                datePos=args.date_pos,
                enableWaterMark=watermark_bool,
            )
            print_success("OSD settings updated", json_mode=args.json)

        elif cmd == "ports":
            onvif = _parse_on_off(args.onvif)
            rtmp = _parse_on_off(args.rtmp)
            rtsp = _parse_on_off(args.rtsp)
            await host.set_net_port(
                enable_onvif=onvif,
                enable_rtmp=rtmp,
                enable_rtsp=rtsp,
            )
            print_success("Network port settings updated", json_mode=args.json)
