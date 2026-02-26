"""Tests for the system command module."""

from __future__ import annotations

import pytest
from argparse import Namespace
from contextlib import asynccontextmanager
from unittest.mock import patch


@pytest.mark.asyncio
async def test_reboot(mock_host):
    """Reboot command should call host.reboot()."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(system_command="reboot", json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.system.connect", mock_connect):
        from reolink_ctl.commands.system import _run

        await _run(args, config)

    mock_host.reboot.assert_awaited_once()


@pytest.mark.asyncio
async def test_firmware_check(mock_host):
    """Firmware check should call check_new_firmware()."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(system_command="firmware", action="check", json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.system.connect", mock_connect):
        from reolink_ctl.commands.system import _run

        await _run(args, config)

    mock_host.check_new_firmware.assert_awaited_once()


@pytest.mark.asyncio
async def test_time_get(mock_host):
    """Getting time should call async_get_time()."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(system_command="time", action="get", json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.system.connect", mock_connect):
        from reolink_ctl.commands.system import _run

        await _run(args, config)

    mock_host.async_get_time.assert_awaited_once()


@pytest.mark.asyncio
async def test_ntp_sync(mock_host):
    """NTP sync should call sync_ntp()."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(system_command="ntp", action="sync", server=None, port=None, json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.system.connect", mock_connect):
        from reolink_ctl.commands.system import _run

        await _run(args, config)

    mock_host.sync_ntp.assert_awaited_once()


@pytest.mark.asyncio
async def test_osd_set_watermark(mock_host):
    """Setting OSD watermark should call set_osd with correct kwargs."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(
        system_command="osd", action="set",
        name_pos=None, date_pos=None, watermark="on", json=False,
    )
    config = {"channel": 0}

    with patch("reolink_ctl.commands.system.connect", mock_connect):
        from reolink_ctl.commands.system import _run

        await _run(args, config)

    mock_host.set_osd.assert_awaited_once_with(
        0, namePos=None, datePos=None, enableWaterMark=True,
    )


@pytest.mark.asyncio
async def test_ports_set_rtsp(mock_host):
    """Setting RTSP port flag should call set_net_port with correct booleans."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(
        system_command="ports", action="set",
        onvif=None, rtmp=None, rtsp="on", json=False,
    )
    config = {"channel": 0}

    with patch("reolink_ctl.commands.system.connect", mock_connect):
        from reolink_ctl.commands.system import _run

        await _run(args, config)

    mock_host.set_net_port.assert_awaited_once_with(
        enable_onvif=None, enable_rtmp=None, enable_rtsp=True,
    )
