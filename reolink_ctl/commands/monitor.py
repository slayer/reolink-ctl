"""Real-time event monitoring via ONVIF long-poll subscription."""

from __future__ import annotations

import asyncio
import json
import signal
import sys
import time
from datetime import datetime, timezone

from reolink_aio.enums import SubType
from reolink_aio.exceptions import SubscriptionError

from reolink_ctl.connection import connect, run_async
from reolink_ctl.output import print_error

# All detectable event types
EVENT_TYPES = ["motion", "people", "vehicle", "dog_cat", "face", "package", "visitor"]

# AI types reported in ai_detection_states (everything except motion/visitor)
_AI_TYPES = {"people", "vehicle", "dog_cat", "face", "package"}

# Minimum remaining seconds before we renew the subscription
_RENEW_MARGIN = 120


def register(subparsers) -> None:
    parser = subparsers.add_parser("monitor", help="Watch for camera events in real time")
    parser.add_argument(
        "-t", "--type", dest="types", action="append", choices=EVENT_TYPES,
        help="Event type to watch (repeatable, omit for all)",
    )
    parser.add_argument(
        "--timeout", type=int, default=0,
        help="Stop after N seconds (0 = run until Ctrl+C)",
    )
    parser.set_defaults(func=run)


def run(args, config) -> None:
    run_async(_run(args, config))


def _snapshot_state(host, channels):
    """Capture current detection state for all channels."""
    state = {}
    for ch in channels:
        state[ch] = {
            "motion": host.motion_detected(ch),
            "visitor": host.visitor_detected(ch),
        }
        ai = host.ai_detection_states(ch)
        for ai_type in _AI_TYPES:
            state[ch][ai_type] = ai.get(ai_type, False)
    return state


def _diff_states(before, after, type_filter):
    """Yield (channel, event_type, new_state) for every changed detection."""
    for ch in after:
        old = before.get(ch, {})
        for event_type, new_val in after[ch].items():
            if old.get(event_type) == new_val:
                continue
            if type_filter and event_type not in type_filter:
                continue
            yield ch, event_type, new_val


def _format_event(ch, event_type, state, json_mode):
    """Format a single event for output."""
    ts = datetime.now(timezone.utc).isoformat()
    if json_mode:
        return json.dumps({
            "timestamp": ts,
            "channel": ch,
            "event": event_type,
            "state": state,
        })
    tag = "ON" if state else "OFF"
    return f"[{ts}] ch{ch} {event_type:<10} {tag}"


async def _run(args, config) -> None:
    type_filter = set(args.types) if args.types else None
    timeout = args.timeout
    json_mode = args.json

    stop = asyncio.Event()

    # Graceful shutdown on SIGINT/SIGTERM
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    async with connect(config) as host:
        channels = host.channels

        # Initial subscribe
        try:
            await host.subscribe(sub_type=SubType.long_poll)
        except SubscriptionError as exc:
            print_error(f"Failed to subscribe: {exc}", json_mode=json_mode)
            return

        try:
            state = _snapshot_state(host, channels)
            deadline = time.monotonic() + timeout if timeout > 0 else None

            while not stop.is_set():
                if deadline and time.monotonic() >= deadline:
                    break

                # Renew if subscription is close to expiring
                if host.renewtimer(SubType.long_poll) < _RENEW_MARGIN:
                    await host.renew(SubType.long_poll)

                try:
                    await host.pull_point_request()
                except SubscriptionError:
                    # Attempt re-subscribe once
                    try:
                        await host.subscribe(sub_type=SubType.long_poll)
                    except SubscriptionError as exc:
                        print_error(f"Re-subscribe failed: {exc}", json_mode=json_mode)
                        return
                    continue

                new_state = _snapshot_state(host, channels)
                for ch, event_type, new_val in _diff_states(state, new_state, type_filter):
                    print(_format_event(ch, event_type, new_val, json_mode), flush=True)
                state = new_state

        finally:
            try:
                await host.unsubscribe(SubType.long_poll)
            except Exception:
                pass  # best-effort cleanup
