"""Webhook management: add, test, remove, disable."""

from __future__ import annotations

from reolink_ctl.connection import connect, run_async
from reolink_ctl.output import print_result, print_error, print_success

ACTIONS = ("add", "test", "remove", "disable")


def register(subparsers) -> None:
    parser = subparsers.add_parser("webhook", help="Webhook management")
    parser.add_argument("action", choices=ACTIONS, help="Webhook action")
    parser.add_argument("url", help="Webhook URL")
    parser.set_defaults(func=run)


def run(args, config) -> None:
    run_async(_run(args, config))


async def _run(args, config) -> None:
    channel = config["channel"]
    url = args.url

    async with connect(config) as host:
        if args.action == "add":
            await host.webhook_add(channel, url)
            print_success(f"Webhook added: {url}", json_mode=args.json)
        elif args.action == "test":
            await host.webhook_test(channel, url)
            print_success(f"Webhook test sent: {url}", json_mode=args.json)
        elif args.action == "remove":
            await host.webhook_remove(channel, url)
            print_success(f"Webhook removed: {url}", json_mode=args.json)
        elif args.action == "disable":
            await host.webhook_disable(channel, url)
            print_success(f"Webhook disabled: {url}", json_mode=args.json)
