"""AI-driven insights helpers."""
from __future__ import annotations

from collections import Counter
from typing import Iterable, List, Tuple

from database.schema import Snapshot
from services.scoring import detect_surging_products


def summarize_trends(snapshots: Iterable[Snapshot]) -> str:
    surging = detect_surging_products(snapshots)
    summary_lines = ["Trend summary:"]
    if surging:
        summary_lines.append(f"Surging IDs: {', '.join(surging)}")
    else:
        summary_lines.append("No surging items detected")
    return "\n".join(summary_lines)


def recommend_keywords(names: Iterable[str], top_k: int = 5) -> List[Tuple[str, int]]:
    words = []
    for name in names:
        words.extend(word.lower() for word in name.split())
    counter = Counter(words)
    return counter.most_common(top_k)
