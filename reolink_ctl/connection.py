"""Async connection management for Reolink cameras."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dotenv import load_dotenv
from reolink_aio.api import Host


@asynccontextmanager
async def connect(config: dict) -> AsyncIterator[Host]:
    """Connect to camera, yield Host, logout on exit."""
    host = Host(
        config["host"],
        config["user"],
        config["password"],
        use_https=False,
        timeout=60,
    )
    try:
        await host.get_host_data()
        yield host
    finally:
        await host.logout()


def resolve_config(args) -> dict:
    """Merge CLI args with .env fallback."""
    load_dotenv()
    return {
        "host": getattr(args, "host", None) or os.getenv("REOLINK_HOST"),
        "user": getattr(args, "user", None) or os.getenv("REOLINK_USER", "admin"),
        "password": getattr(args, "password", None) or os.getenv("REOLINK_PASSWORD"),
        "channel": getattr(args, "channel", 0) or 0,
    }


def run_async(coro):
    """Thin wrapper around asyncio.run()."""
    return asyncio.run(coro)
