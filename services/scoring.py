"""Scoring utilities for ranking and alerting."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, List, Optional


@dataclass
class Snapshot:
    product_id: str
    captured_at: date
    rank: int
    review_count: int = 0
    purchase_count: int = 0
    price: int = 0


def growth_rate(current: int, previous: int) -> float:
    if previous == 0:
        return float("inf") if current > 0 else 0.0
    return (current - previous) / previous


def competitiveness_score(seller_count: int, review_count_value: int) -> float:
    """Lower is better; combines seller saturation and review density."""

    return seller_count * 0.6 + review_count_value * 0.4


def margin_estimate(price: int, cost: int, fees: float = 0.1) -> float:
    gross = price * (1 - fees)
    return gross - cost


def detect_surging_products(
    series: Iterable[Snapshot],
    window: int = 3,
    threshold: float = 0.5,
) -> List[str]:
    """Detect products with rising rank (lower is better) over a rolling window."""

    sorted_series = sorted(series, key=lambda s: (s.product_id, s.captured_at))
    surging: List[str] = []
    buffer: List[Snapshot] = []
    current_product: Optional[str] = None

    for snap in sorted_series:
        if snap.product_id != current_product:
            buffer = []
            current_product = snap.product_id
        buffer.append(snap)
        if len(buffer) < window:
            continue
        ranks = [item.rank for item in buffer[-window:]]
        deltas = [ranks[i] - ranks[i - 1] for i in range(1, len(ranks))]
        improvement = -sum(deltas) / max(len(deltas), 1)
        if improvement >= threshold:
            surging.append(snap.product_id)
    return sorted(set(surging))
