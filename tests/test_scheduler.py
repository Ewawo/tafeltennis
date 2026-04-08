from datetime import UTC, date, datetime
import unittest

from tafeltennis.scheduler import due_to_send, is_blocked_send_day, next_run_at


class SchedulerTests(unittest.TestCase):
    def test_due_to_send_after_scheduled_time(self) -> None:
        now = datetime(2026, 4, 8, 9, 30, tzinfo=UTC)
        self.assertTrue(due_to_send(now, now.timetz().replace(tzinfo=None), None))

    def test_due_to_send_only_once_per_day(self) -> None:
        now = datetime(2026, 4, 8, 9, 30, tzinfo=UTC)
        self.assertFalse(
            due_to_send(
                now,
                now.timetz().replace(tzinfo=None),
                datetime(2026, 4, 8, 9, 31, tzinfo=UTC),
            )
        )

    def test_due_to_send_allows_later_rescheduled_time_same_day(self) -> None:
        now = datetime(2026, 4, 8, 12, 30, tzinfo=UTC)
        self.assertTrue(
            due_to_send(
                now,
                now.timetz().replace(tzinfo=None),
                datetime(2026, 4, 8, 6, 0, tzinfo=UTC),
            )
        )

    def test_next_run_rolls_to_following_day(self) -> None:
        now = datetime(2026, 4, 8, 10, 0, tzinfo=UTC)
        next_run = next_run_at(now, datetime(2026, 4, 8, 9, 0).time())
        self.assertEqual(next_run.isoformat(), "2026-04-09T09:00:00+00:00")

    def test_weekend_is_blocked(self) -> None:
        self.assertTrue(is_blocked_send_day(date(2026, 4, 11)))
        now = datetime(2026, 4, 11, 9, 30, tzinfo=UTC)
        self.assertFalse(due_to_send(now, now.timetz().replace(tzinfo=None), None))

    def test_dutch_public_holiday_is_blocked(self) -> None:
        # 2026-12-25 is Eerste Kerstdag in the Netherlands.
        self.assertTrue(is_blocked_send_day(date(2026, 12, 25)))
        now = datetime(2026, 12, 25, 9, 30, tzinfo=UTC)
        self.assertFalse(due_to_send(now, now.timetz().replace(tzinfo=None), None))

    def test_next_run_skips_weekend_and_holiday(self) -> None:
        # 2026-12-25 is Friday Christmas Day, followed by a weekend.
        now = datetime(2026, 12, 24, 10, 0, tzinfo=UTC)
        next_run = next_run_at(now, datetime(2026, 12, 24, 9, 0).time())
        self.assertEqual(next_run.isoformat(), "2026-12-28T09:00:00+00:00")
