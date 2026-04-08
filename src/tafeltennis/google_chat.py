from __future__ import annotations

from dataclasses import dataclass
import json
from urllib import request
from urllib.error import HTTPError, URLError

from tafeltennis.config import AppConfig


class GoogleChatError(RuntimeError):
    pass


@dataclass(slots=True)
class SendResult:
    ok: bool
    status_code: int
    response_body: str


def build_message_payload(config: AppConfig) -> dict[str, object]:
    return {"text": config.message_text}


def post_message(config: AppConfig) -> SendResult:
    if not config.webhook_url:
        raise GoogleChatError("Google Chat webhook is not configured.")

    payload = json.dumps(build_message_payload(config)).encode("utf-8")
    req = request.Request(
        config.webhook_url,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8")
            return SendResult(True, response.status, body)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GoogleChatError(
            f"Google Chat webhook returned HTTP {exc.code}: {body}"
        ) from exc
    except URLError as exc:
        raise GoogleChatError(f"Could not reach Google Chat webhook: {exc}") from exc
