"""Minimal quickstart to exercise the crawler, scoring, and reporting helpers."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from crawler.naver_store import NaverStoreCrawler, SearchParams
from reports.daily import render_daily_report
from scheduler.jobs import summarize_latest
from services.scoring import Snapshot, detect_surging_products


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    sample_html = project_root / "examples" / "sample_ranking.html"
    if not sample_html.exists():
        raise SystemExit("sample HTML not found; ensure examples/sample_ranking.html exists")

    # 1) Build a ranking URL you could paste into a browser.
    params = SearchParams(category_id="50000000", sort="popular", page=1)
    print("Ranking URL:", params.to_url())

    # 2) Parse embedded JSON from a saved ranking page.
    html = sample_html.read_text(encoding="utf-8")
    products = NaverStoreCrawler.parse_embedded_json(html)
    snapshots = NaverStoreCrawler.as_snapshots(products, captured_at=date.today())
    print(f"Parsed {len(products)} products from sample HTML.")

    # 3) Detect surging items with a simple synthetic history.
    historical = [
        Snapshot(product_id=s.product_id, captured_at=date.today() - timedelta(days=2), rank=s.rank + 5)
        for s in snapshots
    ] + [
        Snapshot(product_id=s.product_id, captured_at=date.today() - timedelta(days=1), rank=s.rank + 2)
        for s in snapshots
    ] + snapshots
    surging = detect_surging_products(historical, window=3, threshold=0.3)
    print("Surging products:", surging)

    # 4) Render a small textual report using the snapshot data.
    report = render_daily_report(snapshots)
    print("\nDaily report:\n", report)

    # 5) Demonstrate how scheduler hooks can be used (with mock data only).
    print("\nScheduler summary preview:\n", summarize_latest(lambda: snapshots))


if __name__ == "__main__":
    main()
