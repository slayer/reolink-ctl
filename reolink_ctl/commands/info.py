"""Device info: model, firmware, channels, storage."""

from __future__ import annotations

from reolink_ctl.connection import connect, run_async
from reolink_ctl.output import print_result, print_error


def register(subparsers) -> None:
    parser = subparsers.add_parser("info", help="Show device information")
    parser.add_argument("--channels", action="store_true", help="Show per-channel info")
    parser.add_argument("--storage", action="store_true", help="Show HDD/storage info")
    parser.set_defaults(func=run)


def run(args, config) -> None:
    run_async(_run(args, config))


async def _run(args, config) -> None:
    async with connect(config) as host:
        # Default overview when no flags given
        if not args.channels and not args.storage:
            data = {
                "model": host.model,
                "serial": host.serial,
                "firmware": host.sw_version,
                "hardware": host.hardware_version,
                "mac": host.mac_address,
                "channels": host.num_channels,
                "nvr": host.is_nvr,
            }
            wifi = host.wifi_signal
            if wifi is not None:
                data["wifi_signal"] = wifi
            print_result(data, json_mode=args.json)
            return

        if args.channels:
            rows = []
            for ch in host.channels:
                rows.append({
                    "channel": ch,
                    "name": host.camera_name(ch),
                    "model": host.camera_model(ch),
                    "online": host.camera_online(ch),
                    "firmware": host.camera_sw_version(ch),
                })
            print_result(rows, json_mode=args.json)

        if args.storage:
            hdds = []
            for idx in host.hdd_list:
                hdds.append({
                    "index": idx,
                    "type": host.hdd_type(idx),
                    "available": host.hdd_available(idx),
                    "storage_gb": round(host.hdd_storage(idx), 1),
                })
            if not hdds:
                print_error("No storage devices found", json_mode=args.json)
            else:
                print_result(hdds, json_mode=args.json)
