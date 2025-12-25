"""Generate daily and weekly textual reports."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Iterable, List

from database.schema import Snapshot
from services.scoring import growth_rate


def build_daily_report(snapshots: Iterable[Snapshot]) -> str:
    by_date = defaultdict(list)
    for snap in snapshots:
        by_date[snap.captured_at].append(snap)
    today = date.today()
    today_snaps = by_date.get(today, [])
    lines: List[str] = [f"Daily report for {today.isoformat()} ({len(today_snaps)} items)"]
    for snap in sorted(today_snaps, key=lambda s: s.rank):
        lines.append(
            f"#{snap.rank:02d} {snap.product_id} price:{snap.price} reviews:{snap.review_count}"
        )
    return "\n".join(lines)


def build_weekly_summary(snapshots: Iterable[Snapshot]) -> str:
    today = date.today()
    week_ago = today - timedelta(days=7)
    recent = [s for s in snapshots if week_ago <= s.captured_at <= today]
    gains = []
    for snap in recent:
        prev = [s for s in recent if s.product_id == snap.product_id and s.captured_at < snap.captured_at]
        if not prev:
            continue
        prev_rank = prev[-1].rank
        gains.append((snap.product_id, growth_rate(prev_rank, snap.rank)))
    gains = sorted(gains, key=lambda g: g[1], reverse=True)[:10]
    lines = [f"Weekly surging candidates ({len(gains)} items)"]
    for pid, change in gains:
        lines.append(f"{pid}: {change:.2f}")
    return "\n".join(lines)
