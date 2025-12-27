"""Slack webhook helper."""
from __future__ import annotations

import json
from urllib import request


def send_slack_message(webhook_url: str, message: str) -> None:
    data = json.dumps({"text": message}).encode()
    req = request.Request(webhook_url, data=data, headers={"Content-Type": "application/json"})
    with request.urlopen(req) as resp:  # noqa: S310 (webhook target is user-provided)
        if resp.status >= 400:
            raise RuntimeError(f"Slack webhook failed: {resp.status}")
