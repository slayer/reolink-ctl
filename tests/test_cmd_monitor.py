"""Tests for the monitor command module."""

from __future__ import annotations

import argparse
import asyncio
import json
from contextlib import asynccontextmanager
from unittest.mock import patch, AsyncMock

from reolink_aio.enums import SubType
from reolink_aio.exceptions import SubscriptionError

from reolink_ctl.commands.monitor import _run

# Short timeout so tests exit quickly after the first meaningful pull
_TIMEOUT = 0.05


def _make_config(channel=0):
    return {"host": "192.168.1.100", "user": "admin", "password": "pass", "channel": channel}


def _make_args(types=None, timeout=_TIMEOUT, json_mode=False):
    return argparse.Namespace(types=types, timeout=timeout, json=json_mode)


def _mock_connect(mock_host):
    @asynccontextmanager
    async def _connect(config):
        yield mock_host
    return _connect


def _pull_then_wait(mock_host, setup_fn):
    """Return a side_effect that runs setup_fn on first call, then sleeps on subsequent calls."""
    call_count = 0

    async def side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            setup_fn(mock_host)
            return
        # Block long enough for the timeout to trigger
        await asyncio.sleep(1)

    return side_effect


# -- Tests -------------------------------------------------------------------


async def test_motion_event(mock_host, capsys):
    """Motion ON event should be printed when motion_detected flips True."""

    def setup(h):
        h.motion_detected.return_value = True

    mock_host.pull_point_request = AsyncMock(side_effect=_pull_then_wait(mock_host, setup))

    with patch("reolink_ctl.commands.monitor.connect", _mock_connect(mock_host)):
        await _run(_make_args(), _make_config())

    output = capsys.readouterr().out
    assert "motion" in output
    assert "ON" in output


async def test_ai_event(mock_host, capsys):
    """AI detection (people) should be printed when ai_detection_states changes."""

    def setup(h):
        h.ai_detection_states.return_value = {"people": True}

    mock_host.pull_point_request = AsyncMock(side_effect=_pull_then_wait(mock_host, setup))

    with patch("reolink_ctl.commands.monitor.connect", _mock_connect(mock_host)):
        await _run(_make_args(), _make_config())

    output = capsys.readouterr().out
    assert "people" in output
    assert "ON" in output


async def test_json_output(mock_host, capsys):
    """--json should produce valid NDJSON with expected keys."""

    def setup(h):
        h.motion_detected.return_value = True

    mock_host.pull_point_request = AsyncMock(side_effect=_pull_then_wait(mock_host, setup))

    with patch("reolink_ctl.commands.monitor.connect", _mock_connect(mock_host)):
        await _run(_make_args(json_mode=True), _make_config())

    output = capsys.readouterr().out.strip()
    event = json.loads(output)
    assert event["event"] == "motion"
    assert event["state"] is True
    assert event["channel"] == 0
    assert "timestamp" in event


async def test_type_filter_excludes_unmatched(mock_host, capsys):
    """--type people should suppress motion events."""

    def setup(h):
        h.motion_detected.return_value = True
        h.ai_detection_states.return_value = {"people": True}

    mock_host.pull_point_request = AsyncMock(side_effect=_pull_then_wait(mock_host, setup))

    with patch("reolink_ctl.commands.monitor.connect", _mock_connect(mock_host)):
        await _run(_make_args(types=["people"], json_mode=True), _make_config())

    output = capsys.readouterr().out.strip()
    event = json.loads(output)
    assert event["event"] == "people"
    # Motion should not appear
    assert "motion" not in capsys.readouterr().out


async def test_subscription_renewal(mock_host):
    """Renew should be called when renewtimer drops below margin."""

    def setup(h):
        pass  # no state change needed

    mock_host.pull_point_request = AsyncMock(side_effect=_pull_then_wait(mock_host, setup))
    mock_host.renewtimer.return_value = 60  # below 120s margin

    with patch("reolink_ctl.commands.monitor.connect", _mock_connect(mock_host)):
        await _run(_make_args(), _make_config())

    mock_host.renew.assert_called_with(SubType.long_poll)


async def test_resubscribe_on_pull_error(mock_host):
    """SubscriptionError during pull should trigger re-subscribe."""
    call_count = 0

    async def pull_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise SubscriptionError("pull failed")
        # Let timeout handle exit
        await asyncio.sleep(1)

    mock_host.pull_point_request = AsyncMock(side_effect=pull_side_effect)

    with patch("reolink_ctl.commands.monitor.connect", _mock_connect(mock_host)):
        await _run(_make_args(), _make_config())

    # subscribe called twice: initial + re-subscribe after error
    assert mock_host.subscribe.call_count == 2


async def test_initial_subscribe_failure(mock_host):
    """If initial subscribe fails, print_error should be called and _run returns."""
    mock_host.subscribe = AsyncMock(side_effect=SubscriptionError("ONVIF unavailable"))

    with patch("reolink_ctl.commands.monitor.connect", _mock_connect(mock_host)):
        with patch("reolink_ctl.commands.monitor.print_error") as mock_err:
            await _run(_make_args(), _make_config())

            mock_err.assert_called_once()
            assert "subscribe" in mock_err.call_args[0][0].lower()

    mock_host.pull_point_request.assert_not_called()


async def test_cleanup_unsubscribe(mock_host):
    """unsubscribe(SubType.long_poll) should always be called in finally."""

    def setup(h):
        pass

    mock_host.pull_point_request = AsyncMock(side_effect=_pull_then_wait(mock_host, setup))

    with patch("reolink_ctl.commands.monitor.connect", _mock_connect(mock_host)):
        await _run(_make_args(), _make_config())

    mock_host.unsubscribe.assert_called_with(SubType.long_poll)
