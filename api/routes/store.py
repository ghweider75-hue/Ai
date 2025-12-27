"""API route helpers for popular and rising products."""
from __future__ import annotations

from datetime import date
from typing import Iterable, List, Optional

from database.schema import Database, Snapshot


def list_popular(db: Database, category_id: Optional[str], limit: int = 20) -> List[Snapshot]:
    rows = db.fetch_recent_snapshots(category_id, limit)
    return [
        Snapshot(
            product_id=row[0],
            captured_at=date.fromisoformat(row[1]),
            rank=row[2],
            price=row[3],
            review_count=row[4],
            purchase_count=row[5],
        )
        for row in rows
    ]


def list_trending(db: Database, category_id: Optional[str], limit: int = 20) -> List[Snapshot]:
    snaps = list(list_popular(db, category_id, limit=limit * 2))
    snaps.sort(key=lambda s: s.rank)
    return snaps[:limit]
