from datetime import date, timedelta

from services.scoring import Snapshot, detect_surging_products, growth_rate, margin_estimate


def test_growth_rate_handles_zero_baseline():
    assert growth_rate(10, 0) == float("inf")
    assert growth_rate(0, 0) == 0.0


def test_margin_estimate():
    assert margin_estimate(1000, 700, fees=0.1) == 200


def test_detect_surging_products():
    base = date.today()
    series = [
        Snapshot(product_id="A", captured_at=base - timedelta(days=2), rank=10),
        Snapshot(product_id="A", captured_at=base - timedelta(days=1), rank=5),
        Snapshot(product_id="A", captured_at=base, rank=3),
        Snapshot(product_id="B", captured_at=base - timedelta(days=2), rank=1),
        Snapshot(product_id="B", captured_at=base - timedelta(days=1), rank=1),
        Snapshot(product_id="B", captured_at=base, rank=1),
    ]
    assert detect_surging_products(series, window=3, threshold=1.0) == ["A"]
