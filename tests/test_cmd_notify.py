"""Tests for the notify command module."""

from __future__ import annotations

import pytest
from argparse import Namespace
from contextlib import asynccontextmanager
from unittest.mock import patch


@pytest.mark.asyncio
async def test_push_on(mock_host):
    """Enabling push should call set_push with True."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(type="push", action="on", json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.notify.connect", mock_connect):
        from reolink_ctl.commands.notify import _run

        await _run(args, config)

    mock_host.set_push.assert_awaited_once_with(0, True)


@pytest.mark.asyncio
async def test_push_status(mock_host):
    """Querying push status should read push_enabled."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(type="push", action="status", json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.notify.connect", mock_connect):
        from reolink_ctl.commands.notify import _run

        await _run(args, config)

    mock_host.push_enabled.assert_called_once_with(0)


@pytest.mark.asyncio
async def test_email_off(mock_host):
    """Disabling email should call set_email with False."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(type="email", action="off", json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.notify.connect", mock_connect):
        from reolink_ctl.commands.notify import _run

        await _run(args, config)

    mock_host.set_email.assert_awaited_once_with(0, False)


@pytest.mark.asyncio
async def test_recording_status(mock_host):
    """Querying recording status should read recording_enabled."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(type="recording", action="status", json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.notify.connect", mock_connect):
        from reolink_ctl.commands.notify import _run

        await _run(args, config)

    mock_host.recording_enabled.assert_called_once_with(0)
