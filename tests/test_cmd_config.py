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
            assert "image" not in data
