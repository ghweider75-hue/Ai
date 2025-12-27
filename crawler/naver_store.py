"""Naver Smart Store crawling utilities.

The crawler focuses on building search/ranking requests and parsing metadata without
making assumptions about the hosting environment. All network operations are
pluggable so that callers can inject authenticated sessions, proxies, or rate
limiters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, List, Mapping, Optional
from urllib.parse import urlencode, urljoin
import json


NAVER_STORE_BASE = "https://search.shopping.naver.com/"


@dataclass
class SearchParams:
    """Parameters used for ranking/search queries.

    Attributes:
        category_id: Naver category identifier.
        start_date: Optional lower bound for ranking window.
        end_date: Optional upper bound for ranking window.
        sort: Ranking method (e.g., "popular", "rising").
        page: Page number for pagination support.
    """

    category_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    sort: str = "popular"
    page: int = 1

    def to_query(self) -> Mapping[str, str]:
        params = {
            "sort": self.sort,
            "pagingIndex": str(self.page),
        }
        if self.category_id:
            params["catId"] = self.category_id
        if self.start_date:
            params["startDate"] = self.start_date.strftime("%Y.%m.%d")
        if self.end_date:
            params["endDate"] = self.end_date.strftime("%Y.%m.%d")
        return params

    def to_url(self) -> str:
        """Build a human-friendly ranking URL for monitoring or manual review."""

        ranking_path = "all" if self.category_id is None else "category"
        base = urljoin(NAVER_STORE_BASE, f"ranking/{ranking_path}")
        return f"{base}?{urlencode(self.to_query())}"


@dataclass
class ProductMeta:
    product_id: str
    name: str
    price: int
    review_count: int
    purchase_count: Optional[int] = None
    image_url: Optional[str] = None
    category_path: List[str] = field(default_factory=list)


@dataclass
class Snapshot:
    product_id: str
    captured_at: date
    rank: Optional[int] = None
    page: Optional[int] = None
    price: Optional[int] = None
    review_count: Optional[int] = None
    purchase_count: Optional[int] = None


class NaverStoreCrawler:
    """Lightweight crawler for Naver Smart Store search/ranking pages.

    The class does not bundle an HTTP client to remain testable and to avoid
    violating robots/ToS in environments where scraping is restricted. The
    :meth:`fetch` method documents the expected interface for external callers.
    """

    def __init__(self, session_fetch):
        """Initialize with a callable that mirrors ``requests.Session.get``.

        Args:
            session_fetch: Callable accepting ``url`` and optional keyword
                arguments such as headers or proxies, returning a response-like
                object with ``status_code`` and ``text`` attributes.
        """

        self.session_fetch = session_fetch

    def fetch(self, params: SearchParams) -> str:
        """Fetch ranking HTML for the given parameters.

        The default implementation uses the injected ``session_fetch`` callable.
        Callers are expected to manage retries, proxy pools, and delay between
        requests to respect Naver's robots.txt and terms of service.
        """

        url = params.to_url()
        response = self.session_fetch(url, headers={"User-Agent": "Mozilla/5.0"})
        if getattr(response, "status_code", 500) >= 400:
            raise RuntimeError(f"Failed to fetch ranking page: {response.status_code}")
        return response.text

    @staticmethod
    def parse_embedded_json(html: str) -> List[ProductMeta]:
        """Extract product metadata from embedded JSON blocks.

        Naver's ranking pages embed product lists inside ``__NEXT_DATA__`` JSON.
        This helper isolates the JSON block and returns a simplified list of
        :class:`ProductMeta` instances. The parsing logic intentionally avoids
        external dependencies and tolerates minor structural changes.
        """

        marker = "__NEXT_DATA__"
        start = html.find(marker)
        if start == -1:
            return []
        data_start = html.find("{", start)
        data_end = html.find("</script>", data_start)
        if data_start == -1 or data_end == -1:
            return []

        payload = html[data_start:data_end]
        try:
            json_data = json.loads(payload)
        except json.JSONDecodeError:
            return []

        return NaverStoreCrawler._extract_products(json_data)

    @staticmethod
    def _extract_products(json_data: object) -> List[ProductMeta]:
        """Traverse JSON to locate product metadata lists.

        The data shape inside ``__NEXT_DATA__`` may drift; instead of relying on
        a single path we scan nested dictionaries/lists for item payloads.
        """

        products: List[ProductMeta] = []

        def walk(node: object) -> None:
            if isinstance(node, dict):
                if "item" in node and isinstance(node["item"], dict):
                    product = NaverStoreCrawler._build_product_meta(node["item"])
                    if product:
                        products.append(product)
                    return
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        # Prefer the structured path when present.
        if isinstance(json_data, dict):
            items = (
                json_data.get("props", {})
                .get("pageProps", {})
                .get("initialState", {})
                .get("products", [])
            )
            if isinstance(items, list) and items:
                walk(items)
                if products:
                    return products

        walk(json_data)
        return products

    @staticmethod
    def _build_product_meta(meta: Mapping[str, object]) -> Optional[ProductMeta]:
        if not isinstance(meta, dict):
            return None
        product_id = str(meta.get("id") or "").strip()
        if not product_id:
            return None
        return ProductMeta(
            product_id=product_id,
            name=str(meta.get("productName") or ""),
            price=int(meta.get("price") or 0),
            review_count=int(meta.get("reviewCount") or 0),
            purchase_count=int(meta.get("purchaseCnt") or 0)
            if meta.get("purchaseCnt") is not None
            else None,
            image_url=meta.get("imageUrl"),
            category_path=list(meta.get("categoryPath") or []),
        )

    @staticmethod
    def as_snapshots(
        products: Iterable[ProductMeta],
        captured_at: date,
        page: int = 1,
    ) -> List[Snapshot]:
        """Convert product metadata into rank snapshots."""

        snapshots: List[Snapshot] = []
        for idx, product in enumerate(products, start=1):
            snapshots.append(
                Snapshot(
                    product_id=product.product_id,
                    captured_at=captured_at,
                    rank=idx,
                    page=page,
                    price=product.price,
                    review_count=product.review_count,
                    purchase_count=product.purchase_count,
                )
            )
        return snapshots
