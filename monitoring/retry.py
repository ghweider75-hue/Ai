"""Retry helpers for network calls."""
from __future__ import annotations

import time
from typing import Callable, TypeVar


T = TypeVar("T")


def with_retry(func: Callable[[], T], attempts: int = 3, delay: float = 1.0) -> T:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return func()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(delay)
    if last_error:
        raise last_error
    raise RuntimeError("Retry exhausted")
