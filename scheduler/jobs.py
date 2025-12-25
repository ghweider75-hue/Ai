"""Lightweight scheduler definitions.

Celery or cron can import these functions to run periodic collection and
reporting. The functions are intentionally small so they are easy to wrap with
specific schedulers.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Callable, Iterable

from crawler.naver_store import NaverStoreCrawler, SearchParams
from database.schema import Database, Product, Snapshot
from reports.daily import build_daily_report
from services.scoring import detect_surging_products


def collect_and_store(
    session_fetch: Callable,
    category_ids: Iterable[str],
    db_path: Path,
    sort: str = "popular",
) -> None:
    crawler = NaverStoreCrawler(session_fetch)
    database = Database(db_path)
    today = date.today()

    for category_id in category_ids:
        params = SearchParams(category_id=category_id, sort=sort)
        html = crawler.fetch(params)
        products = crawler.parse_embedded_json(html)
        database.upsert_products(
            Product(product_id=p.product_id, name=p.name, category_id=category_id)
            for p in products
        )
        snapshots = crawler.as_snapshots(products, captured_at=today)
        database.insert_snapshots(
            Snapshot(
                product_id=s.product_id,
                captured_at=s.captured_at,
                rank=s.rank or 0,
                price=s.price or 0,
                review_count=s.review_count or 0,
                purchase_count=s.purchase_count,
            )
            for s in snapshots
        )


def score_and_report(db_path: Path, notifier: Callable[[str], None], limit: int = 50) -> str:
    db = Database(db_path)
    rows = list(db.fetch_recent_snapshots(category_id=None, limit=limit))
    snapshots = [
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
    surging = detect_surging_products(snapshots)
    if surging:
        notifier(f"Surging products detected: {', '.join(surging)}")
    report = build_daily_report(snapshots)
    notifier(report)
    return report
