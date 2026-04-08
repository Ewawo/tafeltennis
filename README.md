# tafeltennis

Small Python app that sends a scheduled message to a Google Chat space at a
configured UTC time. Non-secret behavior lives in `pyproject.toml`; webhook
secrets live in `.env`.

The schedule is a UTC time-of-day, not a rolling "every 24 hours" timer.
The app checks the current UTC clock and sends once for each UTC day after the
configured time has passed.
It automatically skips Saturdays, Sundays, and Dutch public holidays.

## Configuration

Set the schedule and message in `pyproject.toml`:

```toml
[tool.tafeltennis]
schedule_utc = "18:00"
message_text = "Time to play tafeltennis."
poll_interval_seconds = 30
state_file = ".tafeltennis-state.json"
```

Set the Google Chat webhook secret in `.env`:

```dotenv
GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/.../messages?key=...&token=...
```

You can also store `GOOGLE_CHAT_WEBHOOK_KEY` and `GOOGLE_CHAT_WEBHOOK_TOKEN`
instead of the full webhook URL.

## Usage

Create the environment and sync the project:

```bash
make init
cp .env.example .env
```

Inspect the resolved configuration:

```bash
make show-config
```

Run the scheduler:

```bash
make run
```

Send the message immediately:

```bash
make send
```

Run tests and build a package:

```bash
make test
make build
```
