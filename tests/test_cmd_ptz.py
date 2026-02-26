"""Tests for the ptz command module."""

from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
from unittest.mock import patch

from reolink_ctl.commands.ptz import _run


def _make_config(channel=0):
    return {"host": "192.168.1.100", "user": "admin", "password": "pass", "channel": channel}


def _ptz_args(**kwargs):
    """Build a Namespace for PTZ commands with sensible defaults."""
    defaults = {"json": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


async def test_ptz_move_left_with_speed(mock_host):
    """ptz move left --speed 10 should call set_ptz_command with Left and speed 10."""
    args = _ptz_args(ptz_command="move", direction="left", speed=10)

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        await _run(args, _make_config())

    mock_host.set_ptz_command.assert_awaited_once_with(0, command="Left", speed=10)


async def test_ptz_move_up_default_speed(mock_host):
    """ptz move up (default speed 25) should capitalize direction."""
    args = _ptz_args(ptz_command="move", direction="up", speed=25)

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        await _run(args, _make_config())

    mock_host.set_ptz_command.assert_awaited_once_with(0, command="Up", speed=25)


async def test_ptz_stop(mock_host):
    """ptz stop should call set_ptz_command with Stop."""
    args = _ptz_args(ptz_command="stop")

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        await _run(args, _make_config())

    mock_host.set_ptz_command.assert_awaited_once_with(0, command="Stop")


async def test_ptz_zoom_in(mock_host):
    """ptz zoom in should send ZoomInc command."""
    args = _ptz_args(ptz_command="zoom", zoom_action="in")

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        await _run(args, _make_config())

    mock_host.set_ptz_command.assert_awaited_once_with(0, command="ZoomInc")


async def test_ptz_zoom_out(mock_host):
    """ptz zoom out should send ZoomDec command."""
    args = _ptz_args(ptz_command="zoom", zoom_action="out")

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        await _run(args, _make_config())

    mock_host.set_ptz_command.assert_awaited_once_with(0, command="ZoomDec")


async def test_ptz_zoom_set(mock_host):
    """ptz zoom set 50 should call set_zoom with channel and value."""
    args = _ptz_args(ptz_command="zoom", zoom_action="set", value=50)

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        await _run(args, _make_config())

    mock_host.set_zoom.assert_awaited_once_with(0, 50)


async def test_ptz_focus_auto_on(mock_host):
    """ptz focus auto on should call set_autofocus(ch, True)."""
    args = _ptz_args(ptz_command="focus", focus_action="auto", toggle="on")

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        await _run(args, _make_config())

    mock_host.set_autofocus.assert_awaited_once_with(0, True)


async def test_ptz_focus_auto_off(mock_host):
    """ptz focus auto off should call set_autofocus(ch, False)."""
    args = _ptz_args(ptz_command="focus", focus_action="auto", toggle="off")

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        await _run(args, _make_config())

    mock_host.set_autofocus.assert_awaited_once_with(0, False)


async def test_ptz_focus_set_value(mock_host):
    """ptz focus set 75 should call set_focus(ch, 75)."""
    args = _ptz_args(ptz_command="focus", focus_action="set", value=75)

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        await _run(args, _make_config())

    mock_host.set_focus.assert_awaited_once_with(0, 75)


async def test_ptz_preset_list(mock_host):
    """ptz preset list should call ptz_presets(ch) and print the result."""
    args = _ptz_args(ptz_command="preset", preset_action="list")

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        with patch("reolink_ctl.commands.ptz.print_result") as mock_print:
            await _run(args, _make_config())

    mock_host.ptz_presets.assert_called_once_with(0)
    mock_print.assert_called_once_with({1: "Home", 2: "Gate"}, json_mode=False)


async def test_ptz_preset_goto(mock_host):
    """ptz preset goto 2 should call set_ptz_command with preset=2."""
    args = _ptz_args(ptz_command="preset", preset_action="goto", id=2)

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        await _run(args, _make_config())

    mock_host.set_ptz_command.assert_awaited_once_with(0, preset=2)


async def test_ptz_calibrate(mock_host):
    """ptz calibrate should call ptz_callibrate(ch)."""
    args = _ptz_args(ptz_command="calibrate")

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        await _run(args, _make_config())

    mock_host.ptz_callibrate.assert_awaited_once_with(0)


async def test_ptz_position(mock_host):
    """ptz position should call ptz_pan_position(ch) and print the value."""
    args = _ptz_args(ptz_command="position")

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        with patch("reolink_ctl.commands.ptz.print_result") as mock_print:
            await _run(args, _make_config())

    mock_host.ptz_pan_position.assert_called_once_with(0)
    mock_print.assert_called_once_with({"pan_position": 180}, json_mode=False)


async def test_ptz_track_on_digital(mock_host):
    """ptz track on --method digital should call set_auto_tracking(ch, enable=True, method=2)."""
    args = _ptz_args(ptz_command="track", track_action="on", method="digital")

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        await _run(args, _make_config())

    mock_host.set_auto_tracking.assert_awaited_once_with(0, enable=True, method=2)


async def test_ptz_track_on_pantiltfirst(mock_host):
    """ptz track on --method pantiltfirst should use method=4."""
    args = _ptz_args(ptz_command="track", track_action="on", method="pantiltfirst")

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        await _run(args, _make_config())

    mock_host.set_auto_tracking.assert_awaited_once_with(0, enable=True, method=4)


async def test_ptz_track_off(mock_host):
    """ptz track off should call set_auto_tracking(ch, enable=False)."""
    args = _ptz_args(ptz_command="track", track_action="off")

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        await _run(args, _make_config())

    mock_host.set_auto_tracking.assert_awaited_once_with(0, enable=False)


async def test_ptz_track_limit(mock_host):
    """ptz track limit --left 10 --right 350 should call set_auto_track_limit."""
    args = _ptz_args(ptz_command="track", track_action="limit", left=10, right=350)

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        await _run(args, _make_config())

    mock_host.set_auto_track_limit.assert_awaited_once_with(0, left=10, right=350)


async def test_ptz_no_subcommand_prints_error(mock_host):
    """Calling ptz without a subcommand should print an error (no connect needed)."""
    args = _ptz_args(ptz_command=None)

    with patch("reolink_ctl.commands.ptz.print_error") as mock_err:
        await _run(args, _make_config())

    mock_err.assert_called_once()
    assert "subcommand" in mock_err.call_args[0][0].lower()


async def test_ptz_uses_configured_channel(mock_host):
    """PTZ commands should use the channel from config, not hardcoded 0."""
    args = _ptz_args(ptz_command="stop")

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.ptz.connect", mock_connect):
        await _run(args, _make_config(channel=3))

    mock_host.set_ptz_command.assert_awaited_once_with(3, command="Stop")
