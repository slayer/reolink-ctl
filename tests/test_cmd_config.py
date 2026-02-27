"""Tests for the config command module."""

from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
from unittest.mock import patch, MagicMock

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
            assert "image" not in data


async def test_config_image_section(mock_host):
    """section='image' returns image settings with expected defaults."""

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
    """section='audio' returns audio recording and volume settings."""

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
    """section='detection' returns motion and PIR sensor settings."""

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
    """section='lighting' returns IR, white LED, and status LED settings."""

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
    """section='notifications' returns push, email, ftp, recording, buzzer flags."""

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
    """section='ptz' returns presets, position, guard, and tracking settings."""

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
    """section='system' returns time and storage info from HDD list."""
    # Set up storage mocks not in the default fixture
    mock_host.hdd_list = [0]
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
    """_safe_read wraps errors as None — unsupported props don't crash."""
    mock_host.pir_enabled.side_effect = AttributeError("not supported")

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.config.connect", mock_connect):
        with patch("reolink_ctl.commands.config.print_result") as mock_print:
            await _run(_make_args(section="detection"), _make_config())

            data = mock_print.call_args[0][0]
            assert data["pir_enabled"] is None
