"""Structured output helpers for CLI results."""

from __future__ import annotations

import json
import sys
from typing import Any


def print_result(data: Any, json_mode: bool = False) -> None:
    """Print a dict as aligned key:value pairs, a list as a table, or raw JSON."""
    if json_mode:
        print(json.dumps(data, indent=2, default=str))
        return

    if isinstance(data, dict):
        if not data:
            return
        max_key = max(len(str(k)) for k in data)
        for k, v in data.items():
            print(f"  {str(k):<{max_key}}  {v}")
    elif isinstance(data, list):
        if not data:
            return
        if data and isinstance(data[0], dict):
            # Table format
            keys = list(data[0].keys())
            widths = {k: max(len(k), *(len(str(row.get(k, ""))) for row in data)) for k in keys}
            header = "  ".join(f"{k:<{widths[k]}}" for k in keys)
            print(header)
            print("  ".join("-" * widths[k] for k in keys))
            for row in data:
                print("  ".join(f"{str(row.get(k, '')):<{widths[k]}}" for k in keys))
        else:
            for item in data:
                print(f"  {item}")
    else:
        print(data)


def print_error(msg: str, json_mode: bool = False) -> None:
    """Print error to stderr."""
    if json_mode:
        print(json.dumps({"error": msg}), file=sys.stderr)
    else:
        print(f"Error: {msg}", file=sys.stderr)


def print_success(msg: str, json_mode: bool = False) -> None:
    """Print success confirmation."""
    if json_mode:
        print(json.dumps({"status": "ok", "message": msg}))
    else:
        print(msg)
