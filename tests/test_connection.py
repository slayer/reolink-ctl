"""Tests for reolink_ctl.connection."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from argparse import Namespace

from reolink_ctl.connection import resolve_config, connect


def test_resolve_config_from_args():
    args = Namespace(host="192.168.1.1", user="admin", password="pass", channel=0)
    config = resolve_config(args)
    assert config["host"] == "192.168.1.1"
    assert config["user"] == "admin"
    assert config["password"] == "pass"
    assert config["channel"] == 0


@patch.dict("os.environ", {"REOLINK_HOST": "10.0.0.1", "REOLINK_PASSWORD": "envpass"})
def test_resolve_config_from_env():
    args = Namespace(host=None, user=None, password=None, channel=None)
    config = resolve_config(args)
    assert config["host"] == "10.0.0.1"
    assert config["password"] == "envpass"
    assert config["user"] == "admin"  # default


def test_resolve_config_args_override_env():
    args = Namespace(host="192.168.1.1", user=None, password=None, channel=2)
    with patch.dict("os.environ", {"REOLINK_HOST": "10.0.0.1"}):
        config = resolve_config(args)
    assert config["host"] == "192.168.1.1"
    assert config["channel"] == 2


@pytest.mark.asyncio
async def test_connect_context_manager():
    """connect() calls get_host_data on enter and logout on exit."""
    with patch("reolink_ctl.connection.Host") as MockHost:
        mock_host = MagicMock()
        mock_host.get_host_data = AsyncMock()
        mock_host.logout = AsyncMock()
        MockHost.return_value = mock_host

        config = {"host": "192.168.1.1", "user": "admin", "password": "pass", "channel": 0}
        async with connect(config) as host:
            assert host is mock_host
            mock_host.get_host_data.assert_awaited_once()

        mock_host.logout.assert_awaited_once()


@pytest.mark.asyncio
async def test_connect_logout_on_error():
    """logout is called even if an error occurs inside the context."""
    with patch("reolink_ctl.connection.Host") as MockHost:
        mock_host = MagicMock()
        mock_host.get_host_data = AsyncMock()
        mock_host.logout = AsyncMock()
        MockHost.return_value = mock_host

        config = {"host": "192.168.1.1", "user": "admin", "password": "pass", "channel": 0}
        with pytest.raises(RuntimeError):
            async with connect(config) as host:
                raise RuntimeError("test error")

        mock_host.logout.assert_awaited_once()
