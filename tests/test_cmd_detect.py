"""Tests for the detect command module."""

from __future__ import annotations

import pytest
from argparse import Namespace
from contextlib import asynccontextmanager
from unittest.mock import patch


@pytest.mark.asyncio
async def test_motion_on(mock_host):
    """Enabling motion detection should call set_motion_detection with True."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.detect.connect", mock_connect):
        from reolink_ctl.commands.detect import _motion_on

        await _motion_on(args, config)

    mock_host.set_motion_detection.assert_awaited_once_with(0, True)


@pytest.mark.asyncio
async def test_motion_status(mock_host):
    """Querying motion status should read motion_detected and md_sensitivity."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.detect.connect", mock_connect):
        from reolink_ctl.commands.detect import _motion_status

        await _motion_status(args, config)

    mock_host.motion_detected.assert_called_once_with(0)
    mock_host.md_sensitivity.assert_called_once_with(0)


@pytest.mark.asyncio
async def test_motion_sensitivity(mock_host):
    """Setting motion sensitivity to 30 should call set_md_sensitivity."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(value=30, json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.detect.connect", mock_connect):
        from reolink_ctl.commands.detect import _motion_sensitivity

        await _motion_sensitivity(args, config)

    mock_host.set_md_sensitivity.assert_awaited_once_with(0, 30)


@pytest.mark.asyncio
async def test_ai_sensitivity(mock_host):
    """Setting AI sensitivity should forward type and value."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(value=5, ai_type="people", json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.detect.connect", mock_connect):
        from reolink_ctl.commands.detect import _ai_sensitivity

        await _ai_sensitivity(args, config)

    mock_host.set_ai_sensitivity.assert_awaited_once_with(0, 5, ai_type="people")


@pytest.mark.asyncio
async def test_pir_off(mock_host):
    """Disabling PIR should call set_pir with enable=False."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(action="off", json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.detect.connect", mock_connect):
        from reolink_ctl.commands.detect import _run_pir

        await _run_pir(args, config)

    mock_host.set_pir.assert_awaited_once_with(0, enable=False)
