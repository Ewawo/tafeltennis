from pathlib import Path
import os
import tempfile
import textwrap
import unittest

from tafeltennis.config import ConfigError, load_app_config, parse_time


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_parse_time_supports_seconds(self) -> None:
        parsed = parse_time("13:45:59")
        self.assertEqual(parsed.isoformat(), "13:45:59")

    def test_load_app_config_uses_direct_webhook(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pyproject.toml").write_text(
                textwrap.dedent(
                    """
                    [tool.tafeltennis]
                    schedule_utc = "09:30"
                    message_text = "Play table tennis"
                    poll_interval_seconds = 15
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            (root / ".env").write_text(
                "GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/-/messages?key=x&token=y\n",
                encoding="utf-8",
            )

            config = load_app_config(root / "pyproject.toml", root / ".env")

        self.assertEqual(config.schedule_utc.isoformat(), "09:30:00")
        self.assertEqual(config.message_text, "Play table tennis")
        self.assertEqual(config.poll_interval_seconds, 15)
        self.assertIn("chat.googleapis.com", config.webhook_url)

    def test_load_app_config_builds_url_from_key_and_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pyproject.toml").write_text(
                textwrap.dedent(
                    """
                    [tool.tafeltennis]
                    schedule_utc = "11:15"
                    message_text = "Serve"
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            (root / ".env").write_text(
                "GOOGLE_CHAT_WEBHOOK_KEY=abc\nGOOGLE_CHAT_WEBHOOK_TOKEN=def\n",
                encoding="utf-8",
            )

            config = load_app_config(root / "pyproject.toml", root / ".env")

        self.assertEqual(
            config.webhook_url,
            "https://chat.googleapis.com/v1/spaces/-/messages?key=abc&token=def",
        )

    def test_missing_secret_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pyproject.toml").write_text(
                textwrap.dedent(
                    """
                    [tool.tafeltennis]
                    schedule_utc = "11:15"
                    message_text = "Serve"
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(ConfigError):
                load_app_config(root / "pyproject.toml", root / ".env")

    def test_show_config_mode_allows_missing_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pyproject.toml").write_text(
                textwrap.dedent(
                    """
                    [tool.tafeltennis]
                    schedule_utc = "07:00"
                    message_text = "Morning match"
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            config = load_app_config(
                root / "pyproject.toml",
                root / ".env",
                require_webhook=False,
            )

        self.assertIsNone(config.webhook_url)
