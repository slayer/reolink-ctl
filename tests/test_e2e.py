"""End-to-end tests against a real Reolink camera.

Read-only commands only — nothing that changes camera state.
Auto-skips when REOLINK_HOST is not set, so CI stays green.

Run locally:
    export REOLINK_HOST=<camera-ip>
    export REOLINK_PASSWORD=...
    pytest tests/test_e2e.py -v
"""

from __future__ import annotations

import argparse
import json
import os

import pytest
from dotenv import load_dotenv

load_dotenv()

REOLINK_HOST = os.getenv("REOLINK_HOST")

# Every test in this module gets both markers
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not REOLINK_HOST, reason="REOLINK_HOST not set"),
]


@pytest.fixture(scope="module")
def config():
    """Camera config from env vars — no credentials in code."""
    return {
        "host": REOLINK_HOST,
        "user": os.getenv("REOLINK_USER", "admin"),
        "password": os.getenv("REOLINK_PASSWORD"),
        "channel": int(os.getenv("REOLINK_CHANNEL", "0")),
    }


def _args(**kwargs) -> argparse.Namespace:
    """Build an argparse.Namespace with json=True and given overrides."""
    defaults = {"json": True, "channel": 0}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _parse_json(capsys) -> dict | list:
    """Grab captured stdout and parse as JSON."""
    out = capsys.readouterr().out.strip()
    assert out, "Command produced no output"
    return json.loads(out)


# -- info --------------------------------------------------------------------

async def test_info(config, capsys):
    from reolink_ctl.commands.info import _run

    await _run(_args(channels=False, storage=False), config)
    data = _parse_json(capsys)

    assert "model" in data
    assert "firmware" in data
    assert "mac" in data
    assert "serial" in data
    assert "channels" in data
    assert isinstance(data["channels"], int)
    assert data["channels"] >= 1


async def test_info_channels(config, capsys):
    from reolink_ctl.commands.info import _run

    await _run(_args(channels=True, storage=False), config)
    rows = _parse_json(capsys)

    assert isinstance(rows, list)
    assert len(rows) >= 1
    ch = rows[0]
    assert "name" in ch
    assert "model" in ch
    assert "online" in ch


async def test_info_storage(config, capsys):
    from reolink_ctl.commands.info import _run

    await _run(_args(channels=False, storage=True), config)
    rows = _parse_json(capsys)

    assert isinstance(rows, list)
    assert len(rows) >= 1
    hdd = rows[0]
    assert "type" in hdd
    assert "storage_gb" in hdd
    assert hdd["storage_gb"] > 0


# -- snapshot ----------------------------------------------------------------

async def test_snapshot(config, tmp_path):
    from reolink_ctl.commands.snapshot import _run

    out_file = tmp_path / "test.jpg"
    await _run(_args(output=str(out_file), stream="main"), config)

    data = out_file.read_bytes()
    assert len(data) > 0, "Snapshot is empty"
    # JPEG magic bytes
    assert data[:2] == b"\xff\xd8", "Not a valid JPEG"


# -- stream ------------------------------------------------------------------

async def test_stream_rtsp(config, capsys):
    from reolink_ctl.commands.stream import _run

    await _run(_args(format=None, stream="main"), config)
    data = _parse_json(capsys)

    assert "rtsp" in data
    assert data["rtsp"].startswith("rtsp://")


async def test_stream_rtmp(config, capsys):
    from reolink_ctl.commands.stream import _run

    await _run(_args(format="rtmp", stream="main"), config)
    data = _parse_json(capsys)

    assert "rtmp" in data
    assert "rtmp://" in data["rtmp"]


# -- image -------------------------------------------------------------------

async def test_image_get(config, capsys):
    from reolink_ctl.commands.image import _run_get

    await _run_get(_args(), config)
    data = _parse_json(capsys)

    assert "brightness" in data
    assert "contrast" in data
    assert "daynight" in data
    assert "hdr" in data


# -- detect ------------------------------------------------------------------

async def test_detect_motion_status(config, capsys):
    from reolink_ctl.commands.detect import _motion_status

    await _motion_status(_args(), config)
    data = _parse_json(capsys)

    assert "motion_detected" in data
    assert isinstance(data["motion_detected"], bool)
    assert "sensitivity" in data


# -- light -------------------------------------------------------------------

async def test_light_ir_status(config, capsys):
    from reolink_ctl.commands.light import _run_ir

    await _run_ir(_args(action="status"), config)
    data = _parse_json(capsys)

    assert "ir_enabled" in data
    assert isinstance(data["ir_enabled"], bool)


# -- audio -------------------------------------------------------------------

async def test_audio_record_status(config, capsys):
    from reolink_ctl.commands.audio import _run

    await _run(_args(audio_command="record", action="status"), config)
    data = _parse_json(capsys)

    assert "audio_record" in data
    assert isinstance(data["audio_record"], bool)


async def test_audio_volume_status(config, capsys):
    from reolink_ctl.commands.audio import _run

    await _run(_args(audio_command="volume", value="status"), config)
    data = _parse_json(capsys)

    assert "volume" in data
    assert isinstance(data["volume"], int)
