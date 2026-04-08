from __future__ import annotations

import argparse
from datetime import UTC, datetime

from tafeltennis.config import ConfigError, load_app_config
from tafeltennis.google_chat import GoogleChatError, post_message
from tafeltennis.scheduler import next_run_at, run_scheduler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tafeltennis",
        description="Send a scheduled message to a Google Chat space.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("run", help="Run the UTC scheduler loop.")
    subparsers.add_parser("send-now", help="Send the configured message immediately.")
    subparsers.add_parser("show-config", help="Print the resolved schedule metadata.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "run":
            config = load_app_config()
            scheduled_for = next_run_at(datetime.now(UTC), config.schedule_utc)
            print(f"Scheduler active. Next send at {scheduled_for.isoformat()}.")
            run_scheduler(config)
            return 0

        if args.command == "send-now":
            config = load_app_config()
            result = post_message(config)
            print(f"Message sent with HTTP {result.status_code}.")
            return 0

        if args.command == "show-config":
            config = load_app_config(require_webhook=False)
            scheduled_for = next_run_at(datetime.now(UTC), config.schedule_utc)
            print(f"schedule_utc={config.schedule_utc.isoformat()}")
            print(f"next_run_utc={scheduled_for.isoformat()}")
            print(f"message_text={config.message_text}")
            print(f"state_file={config.state_file}")
            print(f"webhook_configured={'yes' if config.webhook_url else 'no'}")
            return 0
    except (ConfigError, GoogleChatError) as exc:
        parser.error(str(exc))

    return 1
