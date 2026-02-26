"""Audio controls: recording, volume, alarm, siren, quick reply."""

from __future__ import annotations

from reolink_ctl.connection import connect, run_async
from reolink_ctl.output import print_result, print_error, print_success


def register(subparsers) -> None:
    parser = subparsers.add_parser("audio", help="Audio controls")
    audio_command = parser.add_subparsers(dest="audio_command")
    audio_command.required = True

    # audio record <on|off|status>
    rec = audio_command.add_parser("record", help="Audio recording on/off/status")
    rec.add_argument("action", choices=["on", "off", "status"])
    rec.set_defaults(func=run)

    # audio volume <N|status>
    vol = audio_command.add_parser("volume", help="Speaker volume level or status")
    vol.add_argument("value", help="Volume level (int) or 'status'")
    vol.set_defaults(func=run)

    # audio alarm <on|off|status>
    alarm = audio_command.add_parser("alarm", help="Audio alarm on/off/status")
    alarm.add_argument("action", choices=["on", "off", "status"])
    alarm.set_defaults(func=run)

    # audio siren [on|off] [--duration N]
    siren = audio_command.add_parser("siren", help="Trigger or stop the siren")
    siren.add_argument("action", choices=["on", "off"], nargs="?", default="on")
    siren.add_argument("--duration", type=int, default=2, help="Siren duration in seconds (default: 2)")
    siren.set_defaults(func=run)

    # audio reply play <ID>
    reply = audio_command.add_parser("reply", help="Quick-reply playback")
    reply_sub = reply.add_subparsers(dest="reply_command")
    reply_sub.required = True
    play = reply_sub.add_parser("play", help="Play a quick-reply file")
    play.add_argument("file_id", help="Quick-reply file ID")
    play.set_defaults(func=run)


def run(args, config) -> None:
    run_async(_run(args, config))


async def _run(args, config) -> None:
    channel = config["channel"]

    async with connect(config) as host:
        cmd = args.audio_command

        if cmd == "record":
            if args.action == "on":
                await host.set_audio(channel, True)
                print_success("Audio recording enabled", json_mode=args.json)
            elif args.action == "off":
                await host.set_audio(channel, False)
                print_success("Audio recording disabled", json_mode=args.json)
            else:
                enabled = host.audio_record(channel)
                print_result({"audio_record": enabled}, json_mode=args.json)

        elif cmd == "volume":
            if args.value == "status":
                level = host.volume(channel)
                print_result({"volume": level}, json_mode=args.json)
            else:
                try:
                    level = int(args.value)
                except ValueError:
                    print_error("Volume must be an integer or 'status'", json_mode=args.json)
                    return
                await host.set_volume(channel, volume=level)
                print_success(f"Volume set to {level}", json_mode=args.json)

        elif cmd == "alarm":
            if args.action == "on":
                await host.set_audio_alarm(channel, True)
                print_success("Audio alarm enabled", json_mode=args.json)
            elif args.action == "off":
                await host.set_audio_alarm(channel, False)
                print_success("Audio alarm disabled", json_mode=args.json)
            else:
                enabled = host.audio_alarm_enabled(channel)
                print_result({"audio_alarm": enabled}, json_mode=args.json)

        elif cmd == "siren":
            if args.action == "off":
                await host.set_siren(channel, enable=False)
                print_success("Siren stopped", json_mode=args.json)
            else:
                await host.set_siren(channel, enable=True, duration=args.duration)
                print_success(f"Siren activated for {args.duration}s", json_mode=args.json)

        elif cmd == "reply":
            # Only "play" sub-subcommand exists
            await host.play_quick_reply(channel, file_id=int(args.file_id))
            print_success(f"Playing quick reply {args.file_id}", json_mode=args.json)
