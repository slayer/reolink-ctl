"""Tests for the audio command module."""

from __future__ import annotations

import pytest
from argparse import Namespace
from contextlib import asynccontextmanager
from unittest.mock import patch


@pytest.mark.asyncio
async def test_record_on(mock_host):
    """Enabling audio recording should call set_audio with True."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(audio_command="record", action="on", json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.audio.connect", mock_connect):
        from reolink_ctl.commands.audio import _run

        await _run(args, config)

    mock_host.set_audio.assert_awaited_once_with(0, True)


@pytest.mark.asyncio
async def test_record_status(mock_host):
    """Querying record status should read audio_record."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(audio_command="record", action="status", json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.audio.connect", mock_connect):
        from reolink_ctl.commands.audio import _run

        await _run(args, config)

    mock_host.audio_record.assert_called_with(0)


@pytest.mark.asyncio
async def test_volume_set(mock_host):
    """Setting volume to 50 should call set_volume."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(audio_command="volume", value="50", json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.audio.connect", mock_connect):
        from reolink_ctl.commands.audio import _run

        await _run(args, config)

    mock_host.set_volume.assert_awaited_once_with(0, volume=50)


@pytest.mark.asyncio
async def test_volume_status(mock_host):
    """Querying volume status should read volume."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(audio_command="volume", value="status", json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.audio.connect", mock_connect):
        from reolink_ctl.commands.audio import _run

        await _run(args, config)

    mock_host.volume.assert_called_with(0)


@pytest.mark.asyncio
async def test_alarm_off(mock_host):
    """Disabling audio alarm should call set_audio_alarm with False."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(audio_command="alarm", action="off", json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.audio.connect", mock_connect):
        from reolink_ctl.commands.audio import _run

        await _run(args, config)

    mock_host.set_audio_alarm.assert_awaited_once_with(0, False)


@pytest.mark.asyncio
async def test_siren_on_with_duration(mock_host):
    """Activating siren with duration should call set_siren with enable and duration."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(audio_command="siren", action="on", duration=5, json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.audio.connect", mock_connect):
        from reolink_ctl.commands.audio import _run

        await _run(args, config)

    mock_host.set_siren.assert_awaited_once_with(0, enable=True, duration=5)


@pytest.mark.asyncio
async def test_siren_off(mock_host):
    """Stopping siren should call set_siren with enable=False."""

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    args = Namespace(audio_command="siren", action="off", duration=2, json=False)
    config = {"channel": 0}

    with patch("reolink_ctl.commands.audio.connect", mock_connect):
        from reolink_ctl.commands.audio import _run

        await _run(args, config)

    mock_host.set_siren.assert_awaited_once_with(0, enable=False)
