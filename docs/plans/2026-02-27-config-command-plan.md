# Config Command Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a `config` command that dumps all readable camera settings, grouped by section, with optional section filtering.

**Architecture:** Single command module `config.py` with section-builder functions. Each section reads cached Host properties for the current channel. The `system` section additionally calls `async_get_time()`. A positional `section` arg with `choices` filters output to one section.

**Tech Stack:** Python, argparse, reolink_aio Host API, existing output helpers.

---

### Task 1: Create config command with `device` section (TDD)

**Files:**
- Create: `tests/test_cmd_config.py`
- Create: `reolink_ctl/commands/config.py`

**Step 1: Write the failing test**

```python
"""Tests for the config command module."""

from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
from unittest.mock import patch

from reolink_ctl.commands.config import _run


def _make_config(channel=0):
    return {"host": "192.168.1.100", "user": "admin", "password": "pass", "channel": channel}


def _make_args(section=None, json_mode=False):
    return argparse.Namespace(section=section, json=json_mode)


async def test_config_all_returns_grouped_dict(mock_host):
    """No section arg returns all sections as a nested dict."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.config.connect", mock_connect):
        with patch("reolink_ctl.commands.config.print_result") as mock_print:
            await _run(_make_args(), _make_config())

            mock_print.assert_called_once()
            data = mock_print.call_args[0][0]
            assert "device" in data
            assert "image" in data
            assert "audio" in data
            assert "detection" in data
            assert "lighting" in data
            assert "notifications" in data
            assert "ptz" in data
            assert "system" in data


async def test_config_device_section(mock_host):
    """section='device' returns only device info."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.config.connect", mock_connect):
        with patch("reolink_ctl.commands.config.print_result") as mock_print:
            await _run(_make_args(section="device"), _make_config())

            data = mock_print.call_args[0][0]
            assert data["model"] == "RLC-811A"
            assert data["serial"] == "ABCDEF1234567890"
            assert data["firmware"] == "v3.0.0.0_23010100"
            assert data["hardware"] == "IPC_523128M8MP"
            assert data["mac"] == "AA:BB:CC:DD:EE:FF"
            assert data["name"] == "Front Door"
            assert data["online"] is True
            assert data["nvr"] is False
            # No nested keys — this is just the device section
            assert "image" not in data
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cmd_config.py -v -x`
Expected: FAIL (module not found)

**Step 3: Write minimal implementation**

```python
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
    time = await host.async_get_time()
    storage = []
    for idx in host.hdd_list:
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


# Map section names to builder functions
_SECTION_BUILDERS = {
    "device": _device_section,
    "image": _image_section,
    "audio": _audio_section,
    "detection": _detection_section,
    "lighting": _lighting_section,
    "notifications": _notifications_section,
    "ptz": _ptz_section,
    "system": _system_section,  # async — handled specially
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
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cmd_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add reolink_ctl/commands/config.py tests/test_cmd_config.py
git commit -m "feat: add config command with all sections"
```

---

### Task 2: Add remaining unit tests

**Files:**
- Modify: `tests/test_cmd_config.py`

**Step 1: Add tests for each section filter and edge cases**

```python
async def test_config_image_section(mock_host):
    """section='image' returns image settings."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.config.connect", mock_connect):
        with patch("reolink_ctl.commands.config.print_result") as mock_print:
            await _run(_make_args(section="image"), _make_config())

            data = mock_print.call_args[0][0]
            assert data["brightness"] == 128
            assert data["contrast"] == 128
            assert data["daynight"] == "Auto"
            assert data["hdr"] is True


async def test_config_audio_section(mock_host):
    """section='audio' returns audio settings."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.config.connect", mock_connect):
        with patch("reolink_ctl.commands.config.print_result") as mock_print:
            await _run(_make_args(section="audio"), _make_config())

            data = mock_print.call_args[0][0]
            assert data["record"] is True
            assert data["volume"] == 75
            assert data["alarm_enabled"] is False


async def test_config_detection_section(mock_host):
    """section='detection' returns detection settings."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.config.connect", mock_connect):
        with patch("reolink_ctl.commands.config.print_result") as mock_print:
            await _run(_make_args(section="detection"), _make_config())

            data = mock_print.call_args[0][0]
            assert data["motion_detected"] is False
            assert data["sensitivity"] == 25
            assert data["pir_enabled"] is True
            assert data["pir_sensitivity"] == 3


async def test_config_lighting_section(mock_host):
    """section='lighting' returns lighting settings."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.config.connect", mock_connect):
        with patch("reolink_ctl.commands.config.print_result") as mock_print:
            await _run(_make_args(section="lighting"), _make_config())

            data = mock_print.call_args[0][0]
            assert data["ir_enabled"] is True
            assert data["whiteled_on"] is False
            assert data["whiteled_brightness"] == 100
            assert data["status_led"] is True


async def test_config_notifications_section(mock_host):
    """section='notifications' returns notification settings."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.config.connect", mock_connect):
        with patch("reolink_ctl.commands.config.print_result") as mock_print:
            await _run(_make_args(section="notifications"), _make_config())

            data = mock_print.call_args[0][0]
            assert data["push"] is True
            assert data["email"] is False
            assert data["ftp"] is False
            assert data["recording"] is True
            assert data["buzzer"] is False


async def test_config_ptz_section(mock_host):
    """section='ptz' returns PTZ settings."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.config.connect", mock_connect):
        with patch("reolink_ctl.commands.config.print_result") as mock_print:
            await _run(_make_args(section="ptz"), _make_config())

            data = mock_print.call_args[0][0]
            assert data["presets"] == {1: "Home", 2: "Gate"}
            assert data["pan_position"] == 180
            assert data["guard_enabled"] is False
            assert data["auto_track"] is False


async def test_config_system_section(mock_host):
    """section='system' returns time and storage."""
    mock_host.hdd_list = [0]
    from unittest.mock import MagicMock
    mock_host.hdd_type = MagicMock(return_value="SD")
    mock_host.hdd_available = MagicMock(return_value=True)
    mock_host.hdd_storage = MagicMock(return_value=29.3)

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.config.connect", mock_connect):
        with patch("reolink_ctl.commands.config.print_result") as mock_print:
            await _run(_make_args(section="system"), _make_config())

            data = mock_print.call_args[0][0]
            assert "2026-02-26" in data["time"]
            assert len(data["storage"]) == 1
            assert data["storage"][0]["type"] == "SD"


async def test_config_safe_read_returns_none_on_error(mock_host):
    """Properties that raise should return None, not crash."""
    mock_host.pir_enabled.side_effect = AttributeError("not supported")

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.config.connect", mock_connect):
        with patch("reolink_ctl.commands.config.print_result") as mock_print:
            await _run(_make_args(section="detection"), _make_config())

            data = mock_print.call_args[0][0]
            assert data["pir_enabled"] is None
```

**Step 2: Run all config tests**

Run: `uv run pytest tests/test_cmd_config.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_cmd_config.py
git commit -m "test: add unit tests for all config sections"
```

---

### Task 3: Register config command in CLI

**Files:**
- Modify: `reolink_ctl/cli.py:13-31`

**Step 1: Add config to imports and COMMAND_MODULES**

Add `config` to the import list and `COMMAND_MODULES` array in `cli.py`.

**Step 2: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All PASS (existing + new)

**Step 3: Commit**

```bash
git add reolink_ctl/cli.py
git commit -m "feat: register config command in CLI"
```

---

### Task 4: Add E2E test

**Files:**
- Modify: `tests/test_e2e.py`

**Step 1: Add config e2e test**

Add at end of `test_e2e.py`:

```python
# -- config ------------------------------------------------------------------

async def test_config_all(config, capsys):
    from reolink_ctl.commands.config import _run

    await _run(_args(section=None), config)
    data = _parse_json(capsys)

    assert "device" in data
    assert "image" in data
    assert "audio" in data
    assert "detection" in data
    assert "lighting" in data
    assert "notifications" in data
    assert "ptz" in data
    assert "system" in data
    assert "model" in data["device"]


async def test_config_single_section(config, capsys):
    from reolink_ctl.commands.config import _run

    await _run(_args(section="image"), config)
    data = _parse_json(capsys)

    assert "brightness" in data
    assert "contrast" in data
    # Should not have nested sections
    assert "device" not in data
```

**Step 2: Run unit tests to verify nothing broke**

Run: `uv run pytest tests/ -v --ignore=tests/test_e2e.py`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_e2e.py
git commit -m "test: add e2e tests for config command"
```
