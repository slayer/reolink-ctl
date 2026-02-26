"""Tests for the snapshot command module."""

from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
from unittest.mock import patch

from reolink_ctl.commands.snapshot import _run


def _make_config(channel=0):
    return {"host": "192.168.1.100", "user": "admin", "password": "pass", "channel": channel}


def _make_args(output=None, stream="main", json_mode=False):
    return argparse.Namespace(output=output, stream=stream, json=json_mode)


async def test_snapshot_calls_get_snapshot_with_correct_args(mock_host, tmp_path):
    """get_snapshot should be called with the configured channel and stream."""
    out_file = tmp_path / "snap.jpg"

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.snapshot.connect", mock_connect):
        await _run(_make_args(output=str(out_file), stream="sub"), _make_config(channel=2))

    mock_host.get_snapshot.assert_awaited_once_with(2, stream="sub")


async def test_snapshot_writes_bytes_to_output(mock_host, tmp_path):
    """The returned JPEG bytes should be written to the output file."""
    out_file = tmp_path / "test_out.jpg"
    jpeg_bytes = b"\xff\xd8\xff\xe0fake_jpeg"
    mock_host.get_snapshot.return_value = jpeg_bytes

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.snapshot.connect", mock_connect):
        await _run(_make_args(output=str(out_file)), _make_config())

    assert out_file.read_bytes() == jpeg_bytes


async def test_snapshot_default_filename_uses_timestamp(mock_host, tmp_path, monkeypatch):
    """When no --output given, file should be named snapshot_TIMESTAMP.jpg."""
    # Run from tmp_path so the auto-named file lands there
    monkeypatch.chdir(tmp_path)

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.snapshot.connect", mock_connect):
        with patch("reolink_ctl.commands.snapshot.print_success") as mock_success:
            await _run(_make_args(output=None), _make_config())

            mock_success.assert_called_once()
            msg = mock_success.call_args[0][0]
            assert "snapshot_" in msg
            assert ".jpg" in msg

    # Verify a file was actually created in the working dir
    jpg_files = list(tmp_path.glob("snapshot_*.jpg"))
    assert len(jpg_files) == 1
    assert jpg_files[0].read_bytes() == b"\xff\xd8\xff\xe0fake_jpeg"


async def test_snapshot_custom_output_path(mock_host, tmp_path):
    """Explicit --output should write to that exact path."""
    subdir = tmp_path / "photos"
    subdir.mkdir()
    out_file = subdir / "cam01.jpg"

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.snapshot.connect", mock_connect):
        await _run(_make_args(output=str(out_file)), _make_config())

    assert out_file.exists()
    assert out_file.read_bytes() == b"\xff\xd8\xff\xe0fake_jpeg"


async def test_snapshot_empty_data_prints_error(mock_host, tmp_path):
    """When camera returns None, an error should be printed and no file written."""
    mock_host.get_snapshot.return_value = None
    out_file = tmp_path / "should_not_exist.jpg"

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.snapshot.connect", mock_connect):
        with patch("reolink_ctl.commands.snapshot.print_error") as mock_err:
            await _run(_make_args(output=str(out_file)), _make_config())

            mock_err.assert_called_once()
            assert "empty" in mock_err.call_args[0][0].lower()

    assert not out_file.exists()


async def test_snapshot_empty_bytes_prints_error(mock_host, tmp_path):
    """When camera returns empty bytes, it should be treated as empty."""
    mock_host.get_snapshot.return_value = b""
    out_file = tmp_path / "should_not_exist.jpg"

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.snapshot.connect", mock_connect):
        with patch("reolink_ctl.commands.snapshot.print_error") as mock_err:
            await _run(_make_args(output=str(out_file)), _make_config())

            mock_err.assert_called_once()

    assert not out_file.exists()


async def test_snapshot_success_message_includes_size(mock_host, tmp_path):
    """Success message should include the file size in KB."""
    out_file = tmp_path / "sized.jpg"
    # 2048 bytes = 2.0 KB
    mock_host.get_snapshot.return_value = b"\x00" * 2048

    @asynccontextmanager
    async def mock_connect(config):
        yield mock_host

    with patch("reolink_ctl.commands.snapshot.connect", mock_connect):
        with patch("reolink_ctl.commands.snapshot.print_success") as mock_success:
            await _run(_make_args(output=str(out_file)), _make_config())

            msg = mock_success.call_args[0][0]
            assert "2.0 KB" in msg
