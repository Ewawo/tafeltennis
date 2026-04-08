from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from pathlib import Path
import os
import tomllib
from urllib.parse import urlencode


CONFIG_SECTION = ("tool", "tafeltennis")


class ConfigError(ValueError):
    pass


@dataclass(slots=True)
class AppConfig:
    schedule_utc: time
    message_text: str
    poll_interval_seconds: int
    webhook_url: str | None
    state_file: Path


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


def load_app_config(
    pyproject_path: Path = Path("pyproject.toml"),
    env_path: Path = Path(".env"),
    *,
    require_webhook: bool = True,
) -> AppConfig:
    load_env_file(env_path)

    try:
        document = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Missing {pyproject_path}.") from exc

    section = document
    for key in CONFIG_SECTION:
        section = section.get(key)
        if section is None:
            raise ConfigError("Missing [tool.tafeltennis] configuration section.")

    schedule_raw = str(section.get("schedule_utc", "")).strip()
    message_text = str(section.get("message_text", "")).strip()
    poll_interval_seconds = int(section.get("poll_interval_seconds", 30))
    state_file = Path(str(section.get("state_file", ".tafeltennis-state.json")))

    if not schedule_raw:
        raise ConfigError("Set tool.tafeltennis.schedule_utc in pyproject.toml.")
    if not message_text:
        raise ConfigError("Set tool.tafeltennis.message_text in pyproject.toml.")
    if poll_interval_seconds < 5:
        raise ConfigError("tool.tafeltennis.poll_interval_seconds must be at least 5.")

    webhook_url = resolve_webhook_url(required=require_webhook)

    return AppConfig(
        schedule_utc=parse_time(schedule_raw),
        message_text=message_text,
        poll_interval_seconds=poll_interval_seconds,
        webhook_url=webhook_url,
        state_file=state_file,
    )


def parse_time(raw_value: str) -> time:
    parts = raw_value.split(":")
    if len(parts) not in {2, 3}:
        raise ConfigError("schedule_utc must use HH:MM or HH:MM:SS in UTC.")

    try:
        hours, minutes = int(parts[0]), int(parts[1])
        seconds = int(parts[2]) if len(parts) == 3 else 0
        return time(hour=hours, minute=minutes, second=seconds)
    except ValueError as exc:
        raise ConfigError("schedule_utc must contain numeric time components.") from exc


def resolve_webhook_url(*, required: bool) -> str | None:
    direct_url = os.getenv("GOOGLE_CHAT_WEBHOOK_URL", "").strip()
    if direct_url:
        return direct_url

    key = os.getenv("GOOGLE_CHAT_WEBHOOK_KEY", "").strip()
    token = os.getenv("GOOGLE_CHAT_WEBHOOK_TOKEN", "").strip()
    if not key or not token:
        if not required:
            return None
        raise ConfigError(
            "Set GOOGLE_CHAT_WEBHOOK_URL or GOOGLE_CHAT_WEBHOOK_KEY and "
            "GOOGLE_CHAT_WEBHOOK_TOKEN in .env."
        )

    query = urlencode({"key": key, "token": token})
    return f"https://chat.googleapis.com/v1/spaces/-/messages?{query}"
