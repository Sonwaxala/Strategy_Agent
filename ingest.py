"""
Fetches and filters articles from all configured feeds.
"""

import logging
import time
from datetime import datetime, timedelta, timezone

import feedparser

from feeds import FEEDS, RELEVANCE_KEYWORDS
from memory import is_duplicate

logger = logging.getLogger("strategy_agent.ingest")

# Only consider articles published within this lookback window, so a feed
# that hasn't updated in months doesn't dump stale stories into the brief.
LOOKBACK_DAYS = 8

# Be a polite, identifiable client - some publishers 403 generic/empty
# user agents.
USER_AGENT = "StrategyAgent/1.0 (+weekly strategy & M&A digest; contact: sonwabo@edpartner.co.za)"


def _entry_published(entry) -> datetime | None:
    for field in ("published_parsed", "updated_parsed"):
        val = getattr(entry, field, None)
        if val:
            return datetime(*val[:6], tzinfo=timezone.utc)
    return None


def _is_relevant(title: str, summary: str) -> bool:
    text = f"{title} {summary}".lower()
    return any(kw in text for kw in RELEVANCE_KEYWORDS)


def fetch_all() -> list[dict]:
    """Returns a deduplicated, relevance-filtered, recency-filtered list of
    article dicts: {title, url, summary, source, tier, published}."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    collected = []
    seen_in_this_run = set()  # catch duplicates across feeds within one run

    for feed_cfg in FEEDS:
        name, url, tier = feed_cfg["name"], feed_cfg["url"], feed_cfg["tier"]
        try:
            parsed = feedparser.parse(url, agent=USER_AGENT)
            if parsed.bozo and not parsed.entries:
                logger.warning("Feed failed to parse (skipping): %s — %s", name, parsed.get("bozo_exception"))
                continue
        except Exception as e:
            logger.warning("Feed fetch error (skipping): %s — %s", name, e)
            continue

        for entry in parsed.entries:
            title = getattr(entry, "title", "").strip()
            link = getattr(entry, "link", "").strip()
            summary = getattr(entry, "summary", getattr(entry, "description", "")).strip()

            if not title or not link:
                continue

            published = _entry_published(entry)
            if published and published < cutoff:
                continue

            if not _is_relevant(title, summary):
                continue

            if link in seen_in_this_run:
                continue
            seen_in_this_run.add(link)

            if is_duplicate(link, title):
                continue

            collected.append({
                "title": title,
                "url": link,
                "summary": summary,
                "source": name,
                "tier": tier,
                "published": published.isoformat() if published else None,
            })

        time.sleep(0.5)  # light politeness delay between feed fetches

    logger.info("Collected %d new, relevant, non-duplicate articles across %d feeds",
                len(collected), len(FEEDS))
    return collected
