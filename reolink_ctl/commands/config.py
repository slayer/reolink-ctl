"""Camera configuration dump: all readable settings grouped by section."""

from __future__ import annotations

from reolink_ctl.connection import connect, run_async
from reolink_ctl.output import print_result

SECTIONS = [
    "device", "image", "audio", "detection",
    "lighting", "notifications", "ptz", "system",
]


def register(subparsers) -> None:
    parser = subparsers.add_parser("config", help="Show camera configuration")
    parser.add_argument(
        "section", nargs="?", choices=SECTIONS, default=None,
        help="Show only this section (default: all)",
    )
    parser.set_defaults(func=run)


def run(args, config) -> None:
    run_async(_run(args, config))


def _safe_read(fn, *a, **kw):
    """Call a host property/method, return None on error."""
    try:
        return fn(*a, **kw)
    except Exception:
        return None


def _device_section(host, ch):
    data = {
        "model": host.model,
        "serial": host.serial,
        "firmware": host.sw_version,
        "hardware": host.hardware_version,
        "mac": host.mac_address,
        "nvr": host.is_nvr,
        "name": _safe_read(host.camera_name, ch),
        "online": _safe_read(host.camera_online, ch),
    }
    wifi = host.wifi_signal
    if wifi is not None:
        data["wifi_signal"] = wifi
    return data


def _image_section(host, ch):
    return {
        "brightness": _safe_read(host.image_brightness, ch),
        "contrast": _safe_read(host.image_contrast, ch),
        "saturation": _safe_read(host.image_saturation, ch),
        "sharpness": _safe_read(host.image_sharpness, ch),
        "hue": _safe_read(host.image_hue, ch),
        "daynight": _safe_read(host.daynight_state, ch),
        "hdr": _safe_read(host.HDR_on, ch),
    }


def _audio_section(host, ch):
    return {
        "record": _safe_read(host.audio_record, ch),
        "volume": _safe_read(host.volume, ch),
        "alarm_enabled": _safe_read(host.audio_alarm_enabled, ch),
    }


def _detection_section(host, ch):
    return {
        "motion_detected": _safe_read(host.motion_detected, ch),
        "sensitivity": _safe_read(host.md_sensitivity, ch),
        "pir_enabled": _safe_read(host.pir_enabled, ch),
        "pir_sensitivity": _safe_read(host.pir_sensitivity, ch),
    }


def _lighting_section(host, ch):
    return {
        "ir_enabled": _safe_read(host.ir_enabled, ch),
        "whiteled_on": _safe_read(host.whiteled_state, ch),
        "whiteled_mode": _safe_read(host.whiteled_mode, ch),
        "whiteled_brightness": _safe_read(host.whiteled_brightness, ch),
        "status_led": _safe_read(host.status_led_enabled, ch),
    }


def _notifications_section(host, ch):
    return {
        "push": _safe_read(host.push_enabled, ch),
        "email": _safe_read(host.email_enabled, ch),
        "ftp": _safe_read(host.ftp_enabled, ch),
        "recording": _safe_read(host.recording_enabled, ch),
        "buzzer": _safe_read(host.buzzer_enabled, ch),
    }


def _ptz_section(host, ch):
    return {
        "presets": _safe_read(host.ptz_presets, ch),
        "pan_position": _safe_read(host.ptz_pan_position, ch),
        "guard_enabled": _safe_read(host.ptz_guard_enabled, ch),
        "guard_time": _safe_read(host.ptz_guard_time, ch),
        "auto_track": _safe_read(host.auto_track_enabled, ch),
    }


async def _system_section(host, ch):
    try:
        time = await host.async_get_time()
    except Exception:
        time = None
    storage = []
    for idx in (host.hdd_list or []):
        storage.append({
            "index": idx,
            "type": _safe_read(host.hdd_type, idx),
            "available": _safe_read(host.hdd_available, idx),
            "storage_gb": round(_safe_read(host.hdd_storage, idx) or 0, 1),
        })
    return {
        "time": str(time) if time else None,
        "storage": storage,
    }


# system section is async, handled separately in _run
_SECTION_BUILDERS = {
    "device": _device_section,
    "image": _image_section,
    "audio": _audio_section,
    "detection": _detection_section,
    "lighting": _lighting_section,
    "notifications": _notifications_section,
    "ptz": _ptz_section,
    "system": _system_section,
}


async def _run(args, config) -> None:
    ch = config["channel"]
    async with connect(config) as host:
        if args.section:
            builder = _SECTION_BUILDERS[args.section]
            if args.section == "system":
                data = await builder(host, ch)
            else:
                data = builder(host, ch)
            print_result(data, json_mode=args.json)
        else:
            result = {}
            for name, builder in _SECTION_BUILDERS.items():
                if name == "system":
                    result[name] = await builder(host, ch)
                else:
                    result[name] = builder(host, ch)
            print_result(result, json_mode=args.json)
