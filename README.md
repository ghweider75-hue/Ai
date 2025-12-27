# Ai

Prototype architecture for monitoring Naver Smart Store ranking pages, storing
snapshots, and surfacing insights. The codebase is intentionally minimal to keep
core responsibilities isolated and testable without external services.

## Components
- `crawler/naver_store.py`: builds ranking URLs, fetches HTML via injected
  session, and parses embedded JSON to product metadata and snapshots.
- `database/schema.py`: SQLite schema for categories, products, and snapshots
  with helper methods for upsert and retrieval.
- `scheduler/jobs.py`: callable hooks that schedulers (Celery, cron) can use to
  run periodic collection and reporting.
- `services/scoring.py`: growth, competitiveness, margin, and surge detection
  helpers.
- `reports/daily.py`: daily and weekly textual summaries of snapshot trends.
- `notifier/slack.py`: minimal Slack webhook sender for alerts.
- `api/routes/store.py`: helpers to serve popular/trending snapshot data to an
  API layer.
- `ai/insights.py`: keyword recommendation and trend summaries built on stored
  data.
- `monitoring/retry.py`: generic retry wrapper for network calls.

## Quickstart (local-only sample)
The repository ships with an offline sample ranking page so you can verify the
crawler, scoring, and reporting flows without hitting live Naver endpoints.

1. Create a virtual environment (optional but recommended) and activate it.
2. Run the quickstart script:
   ```bash
   python scripts/quickstart.py
   ```
   You should see a ranking URL, parsed product count, a list of surging
   products (based on synthetic history), and a small text report.

## Running tests
Execute the unit tests with:

```bash
python -m pytest
```

## Using a real HTTP client
To crawl live pages, inject your own HTTP client into `NaverStoreCrawler`, for
example with `requests.Session.get`:

```python
import requests
from crawler.naver_store import NaverStoreCrawler, SearchParams

session = requests.Session()
crawler = NaverStoreCrawler(session.get)
html = crawler.fetch(SearchParams(category_id="50000000", sort="popular"))
products = NaverStoreCrawler.parse_embedded_json(html)
```

Handle rate limits, robots.txt, and Naver terms of service according to your
environmental and legal requirements.
