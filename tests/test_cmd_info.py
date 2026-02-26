"""Tests for the info command module."""

from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
from unittest.mock import patch, MagicMock

from reolink_ctl.commands.info import _run


def _make_config(channel=0):
    return {"host": "192.168.1.100", "user": "admin", "password": "pass", "channel": channel}


def _make_args(channels=False, storage=False, json_mode=False):
    return argparse.Namespace(channels=channels, storage=storage, json=json_mode)


async def test_info_default_returns_device_overview(mock_host):
    """Default invocation (no flags) should return model, serial, firmware, etc."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.info.connect", mock_connect):
        # Capture print_result call to inspect the data dict
        with patch("reolink_ctl.commands.info.print_result") as mock_print:
            await _run(_make_args(), _make_config())

            mock_print.assert_called_once()
            data = mock_print.call_args[0][0]
            assert data["model"] == "RLC-811A"
            assert data["serial"] == "ABCDEF1234567890"
            assert data["firmware"] == "v3.0.0.0_23010100"
            assert data["hardware"] == "IPC_523128M8MP"
            assert data["mac"] == "AA:BB:CC:DD:EE:FF"
            assert data["channels"] == 1
            assert data["nvr"] is False


async def test_info_default_includes_wifi_when_present(mock_host):
    """wifi_signal should be included in the result when the host reports it."""
    mock_host.wifi_signal = -42

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.info.connect", mock_connect):
        with patch("reolink_ctl.commands.info.print_result") as mock_print:
            await _run(_make_args(), _make_config())

            data = mock_print.call_args[0][0]
            assert data["wifi_signal"] == -42


async def test_info_default_omits_wifi_when_none(mock_host):
    """wifi_signal should not appear when it is None."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.info.connect", mock_connect):
        with patch("reolink_ctl.commands.info.print_result") as mock_print:
            await _run(_make_args(), _make_config())

            data = mock_print.call_args[0][0]
            assert "wifi_signal" not in data


async def test_info_channels_flag(mock_host):
    """--channels should list per-channel name, model, online status, firmware."""
    mock_host.channels = [0, 1]
    # Channel 1 overrides
    mock_host.camera_name.side_effect = lambda ch: {0: "Front Door", 1: "Backyard"}[ch]
    mock_host.camera_model.side_effect = lambda ch: {0: "RLC-811A", 1: "RLC-520A"}[ch]
    mock_host.camera_online.side_effect = lambda ch: {0: True, 1: False}[ch]
    mock_host.camera_sw_version.side_effect = lambda ch: {0: "v3.0.0.0_23010100", 1: "v2.0.0.0"}[ch]

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.info.connect", mock_connect):
        with patch("reolink_ctl.commands.info.print_result") as mock_print:
            await _run(_make_args(channels=True), _make_config())

            mock_print.assert_called_once()
            rows = mock_print.call_args[0][0]
            assert isinstance(rows, list)
            assert len(rows) == 2
            assert rows[0]["name"] == "Front Door"
            assert rows[0]["channel"] == 0
            assert rows[1]["name"] == "Backyard"
            assert rows[1]["online"] is False


async def test_info_storage_with_hdds(mock_host):
    """--storage should read hdd_list and report type, available, storage_gb."""
    mock_host.hdd_list = [0, 1]
    mock_host.hdd_type = MagicMock(side_effect=lambda idx: {0: "HDD", 1: "SD"}[idx])
    mock_host.hdd_available = MagicMock(side_effect=lambda idx: {0: True, 1: True}[idx])
    mock_host.hdd_storage = MagicMock(side_effect=lambda idx: {0: 931.5, 1: 29.3}[idx])

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.info.connect", mock_connect):
        with patch("reolink_ctl.commands.info.print_result") as mock_print:
            await _run(_make_args(storage=True), _make_config())

            mock_print.assert_called_once()
            hdds = mock_print.call_args[0][0]
            assert len(hdds) == 2
            assert hdds[0]["type"] == "HDD"
            assert hdds[0]["storage_gb"] == 931.5
            assert hdds[1]["type"] == "SD"
            assert hdds[1]["storage_gb"] == 29.3


async def test_info_storage_empty(mock_host):
    """--storage with no HDDs should print an error instead of results."""
    mock_host.hdd_list = []

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.info.connect", mock_connect):
        with patch("reolink_ctl.commands.info.print_error") as mock_err:
            await _run(_make_args(storage=True), _make_config())

            mock_err.assert_called_once()
            assert "No storage" in mock_err.call_args[0][0]


async def test_info_channels_and_storage_together(mock_host):
    """Both flags at once should produce both channel rows and storage output."""
    mock_host.channels = [0]
    mock_host.hdd_list = [0]
    mock_host.hdd_type = MagicMock(return_value="HDD")
    mock_host.hdd_available = MagicMock(return_value=True)
    mock_host.hdd_storage = MagicMock(return_value=500.0)

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.info.connect", mock_connect):
        with patch("reolink_ctl.commands.info.print_result") as mock_print:
            await _run(_make_args(channels=True, storage=True), _make_config())

            # print_result called twice: once for channels, once for storage
            assert mock_print.call_count == 2
            channel_rows = mock_print.call_args_list[0][0][0]
            hdd_rows = mock_print.call_args_list[1][0][0]
            assert isinstance(channel_rows, list)
            assert isinstance(hdd_rows, list)
