"""Tests for CLI argument parsing and dispatch."""

import pytest
from unittest.mock import patch

from reolink_ctl.cli import build_parser


def test_build_parser_has_all_commands():
    parser = build_parser()
    # Parse --help would exit, so just check subparser choices
    # Access the subparsers action to check registered commands
    subparsers_actions = [
        action for action in parser._subparsers._actions
        if hasattr(action, '_parser_class')
    ]
    assert len(subparsers_actions) == 1
    choices = subparsers_actions[0].choices
    expected = [
        "info", "snapshot", "stream", "download", "ptz",
        "light", "image", "detect", "audio", "notify", "webhook", "system",
    ]
    for cmd in expected:
        assert cmd in choices, f"Missing command: {cmd}"


def test_global_flags():
    parser = build_parser()
    args = parser.parse_args(["-H", "192.168.1.1", "-u", "admin", "-p", "pass", "--json", "info"])
    assert args.host == "192.168.1.1"
    assert args.user == "admin"
    assert args.password == "pass"
    assert args.json is True
    assert args.command == "info"


def test_download_subcommand_args():
    parser = build_parser()
    args = parser.parse_args(["download", "--person", "--since", "2h", "--dry-run"])
    assert args.command == "download"
    assert args.person is True
    assert args.since == "2h"
    assert args.dry_run is True


def test_no_command_returns_none():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.command is None


def test_channel_default():
    parser = build_parser()
    args = parser.parse_args(["info"])
    assert args.channel == 0


def test_channel_override():
    parser = build_parser()
    args = parser.parse_args(["-c", "2", "info"])
    assert args.channel == 2
