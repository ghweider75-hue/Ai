"""SQLite schema and helpers for product snapshots."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Iterator, Optional, Tuple


@dataclass
class Product:
    product_id: str
    name: str
    category_id: Optional[str]


@dataclass
class Snapshot:
    product_id: str
    captured_at: date
    rank: int
    price: int
    review_count: int
    purchase_count: Optional[int]


SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category_id TEXT,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS snapshots (
    product_id TEXT NOT NULL,
    captured_at DATE NOT NULL,
    rank INTEGER,
    price INTEGER,
    review_count INTEGER,
    purchase_count INTEGER,
    PRIMARY KEY (product_id, captured_at),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
"""


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def upsert_products(self, products: Iterable[Product]) -> None:
        with self.connection() as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO products (id, name, category_id) VALUES (?, ?, ?)",
                [(p.product_id, p.name, p.category_id) for p in products],
            )

    def insert_snapshots(self, snapshots: Iterable[Snapshot]) -> None:
        with self.connection() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO snapshots (
                    product_id, captured_at, rank, price, review_count, purchase_count
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        s.product_id,
                        s.captured_at.isoformat(),
                        s.rank,
                        s.price,
                        s.review_count,
                        s.purchase_count,
                    )
                    for s in snapshots
                ],
            )

    def fetch_recent_snapshots(
        self, category_id: Optional[str], limit: int = 50
    ) -> Iterator[Tuple[str, str, int, int, int, Optional[int]]]:
        query = "SELECT product_id, captured_at, rank, price, review_count, purchase_count FROM snapshots"
        params: Tuple = ()
        if category_id:
            query += " JOIN products ON products.id = snapshots.product_id WHERE products.category_id = ?"
            params = (category_id,)
        query += " ORDER BY captured_at DESC LIMIT ?"
        params += (limit,)
        with self.connection() as conn:
            for row in conn.execute(query, params):
                yield row
