"""
Strategy Agent — main entrypoint.

Pipeline: ingest (RSS, dedup, relevance filter) -> analyze (Claude) ->
build report (HTML) -> email (Gmail SMTP) -> record what was sent (so
next week's dedup check knows about it).

Run manually:   python main.py
Run in CI:      triggered by .github/workflows/weekly_report.yml every
                 Monday 09:30 SAST (07:30 UTC).
"""

import logging
import sys
from datetime import datetime, timezone

from analyze import analyze
from deliver import send_report
from ingest import fetch_all
from memory import init_db, record_run, record_sent
from report import build_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("strategy_agent.main")


def run():
    logger.info("Strategy Agent run starting")
    init_db()

    raw_articles = fetch_all()
    if not raw_articles:
        logger.warning("No new, relevant, non-duplicate articles found this week. "
                        "No report will be sent.")
        record_run(items_included=0, items_filtered_duplicate=0)
        return

    logger.info("Sending %d articles to Claude for analysis", len(raw_articles))
    analyzed = analyze(raw_articles)

    items_by_tier: dict[str, list] = {}
    for item in analyzed:
        items_by_tier.setdefault(item["tier"], []).append(item)

    report_date = datetime.now(timezone.utc)
    html = build_report(items_by_tier, report_date)

    subject = f"Strategy Agent — Weekly Brief — {report_date.strftime('%d %b %Y')}"
    send_report(html, subject)

    record_sent(analyzed)
    record_run(items_included=len(analyzed), items_filtered_duplicate=0)

    logger.info("Run complete: %d items delivered", len(analyzed))


if __name__ == "__main__":
    try:
        run()
    except Exception:
        logger.exception("Strategy Agent run failed")
        sys.exit(1)
