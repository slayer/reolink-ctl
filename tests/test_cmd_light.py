"""Tests for the light command module."""

from __future__ import annotations

import pytest
from argparse import Namespace
from contextlib import asynccontextmanager
from unittest.mock import patch


@pytest.mark.asyncio
async def test_ir_on(mock_host):
    """Enabling IR should call set_ir_lights with True."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(action="on", json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.light.connect", mock_connect):
        from reolink_ctl.commands.light import _run_ir

        await _run_ir(args, config)

    mock_host.set_ir_lights.assert_awaited_once_with(0, True)


@pytest.mark.asyncio
async def test_ir_status(mock_host):
    """Querying IR status should read ir_enabled."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(action="status", json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.light.connect", mock_connect):
        from reolink_ctl.commands.light import _run_ir

        await _run_ir(args, config)

    mock_host.ir_enabled.assert_called_once_with(0)


@pytest.mark.asyncio
async def test_whiteled_set_flags(mock_host):
    """Setting whiteled with explicit flags should call set_whiteled."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(state="on", brightness=80, mode=None, json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.light.connect", mock_connect):
        from reolink_ctl.commands.light import _run_whiteled

        await _run_whiteled(args, config)

    mock_host.set_whiteled.assert_awaited_once_with(
        0, state=True, brightness=80, mode=None,
    )


@pytest.mark.asyncio
async def test_whiteled_no_flags_reads_status(mock_host):
    """Calling whiteled with no flags should read current state."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    # All flags absent -> read mode
    args = Namespace(state=None, brightness=None, mode=None, json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.light.connect", mock_connect):
        from reolink_ctl.commands.light import _run_whiteled

        await _run_whiteled(args, config)

    mock_host.whiteled_state.assert_called_once_with(0)
    mock_host.whiteled_mode.assert_called_once_with(0)
    mock_host.whiteled_brightness.assert_called_once_with(0)


@pytest.mark.asyncio
async def test_status_led_auto(mock_host):
    """Setting status-led to 'auto' should call set_status_led with 'auto'."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(mode_or_status="auto", json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.light.connect", mock_connect):
        from reolink_ctl.commands.light import _run_status_led

        await _run_status_led(args, config)

    mock_host.set_status_led.assert_awaited_once_with(0, "auto")
