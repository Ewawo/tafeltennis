from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
import json
from pathlib import Path
import time

import holidays

from tafeltennis.config import AppConfig
from tafeltennis.google_chat import post_message


@dataclass(slots=True)
class SchedulerState:
    # Timestamp of the most recent successful send. This is only used to
    # confirm whether today's configured UTC send time has already been served.
    last_sent_at: datetime | None = None


def load_state(path: Path) -> SchedulerState:
    if not path.exists():
        return SchedulerState()

    payload = json.loads(path.read_text(encoding="utf-8"))
    last_sent_at = payload.get("last_sent_at")
    if last_sent_at:
        return SchedulerState(last_sent_at=datetime.fromisoformat(last_sent_at))

    # Backward compatibility for the older date-only state format.
    last_sent_on = payload.get("last_sent_on")
    if last_sent_on:
        return SchedulerState(
            last_sent_at=datetime.combine(
                date.fromisoformat(last_sent_on),
                datetime.min.time(),
                tzinfo=UTC,
            )
        )

    return SchedulerState()


def save_state(path: Path, state: SchedulerState) -> None:
    path.write_text(
        json.dumps(
            {
                "last_sent_at": (
                    state.last_sent_at.isoformat() if state.last_sent_at else None
                )
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def due_to_send(now: datetime, schedule_time, last_sent_at: datetime | None) -> bool:
    # The schedule is a UTC time-of-day. Send once after today's target time
    # unless that specific daily slot has already been satisfied.
    if is_blocked_send_day(now.date()):
        return False

    scheduled_for_today = datetime.combine(now.date(), schedule_time, tzinfo=UTC)
    return now >= scheduled_for_today and (
        last_sent_at is None or last_sent_at < scheduled_for_today
    )


def next_run_at(now: datetime, schedule_time) -> datetime:
    # Compute the next occurrence of the configured UTC time-of-day.
    candidate_day = now.date()
    scheduled_for_today = datetime.combine(candidate_day, schedule_time, tzinfo=UTC)

    if now >= scheduled_for_today:
        candidate_day += timedelta(days=1)

    while is_blocked_send_day(candidate_day):
        candidate_day += timedelta(days=1)

    return datetime.combine(candidate_day, schedule_time, tzinfo=UTC)


def is_blocked_send_day(day: date) -> bool:
    if day.weekday() >= 5:
        return True

    return day in holidays.country_holidays("NL")


def run_scheduler(config: AppConfig) -> None:
    state = load_state(config.state_file)

    while True:
        now = datetime.now(UTC)
        if due_to_send(now, config.schedule_utc, state.last_sent_at):
            post_message(config)
            state.last_sent_at = now
            save_state(config.state_file, state)

        time.sleep(config.poll_interval_seconds)
