"""
Builds the clean, professional HTML email report from analyzed articles,
grouped South Africa -> Africa -> Global.

~30-minute read target: roughly 25-35 articles at 3-5 sentences each,
which is what the relevance + lookback filters in ingest.py are tuned to
produce in a typical week. If volume runs heavy, items beyond a sane cap
per tier are trimmed (highest-relevance / most recent kept) to protect
the read-time promise rather than silently producing an hour-long report.
"""

from datetime import datetime
from html import escape

from feeds import TIER_ORDER

MAX_ITEMS_PER_TIER = 14  # keeps total report in the ~30 min read range


def _tier_section(tier: str, items: list[dict]) -> str:
    if not items:
        return ""
    items = items[:MAX_ITEMS_PER_TIER]
    cards = []
    for item in items:
        cards.append(f"""
        <div style="padding:18px 0;border-bottom:1px solid #e5e5e5;">
          <div style="font-size:11px;letter-spacing:0.05em;text-transform:uppercase;color:#888;margin-bottom:6px;">
            {escape(item['source'])}
          </div>
          <div style="font-size:17px;font-weight:600;color:#1a1a1a;margin-bottom:8px;line-height:1.35;">
            {escape(item['title'])}
          </div>
          <div style="font-size:14px;color:#333;line-height:1.6;margin-bottom:10px;">
            {escape(item['summary'])}
          </div>
          <a href="{escape(item['url'])}" style="font-size:13px;color:#0a5c36;text-decoration:none;font-weight:600;">
            Read full article &rarr;
          </a>
        </div>""")

    return f"""
    <tr><td style="padding:30px 0 10px 0;">
      <div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:#0a5c36;font-weight:700;border-bottom:2px solid #0a5c36;padding-bottom:8px;">
        {escape(tier)}
      </div>
    </td></tr>
    <tr><td>{''.join(cards)}</td></tr>"""


def build_report(items_by_tier: dict, report_date: datetime) -> str:
    total_items = sum(len(v) for v in items_by_tier.values())
    sections = "".join(_tier_section(tier, items_by_tier.get(tier, [])) for tier in TIER_ORDER)

    date_str = report_date.strftime("%A, %d %B %Y")

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f4f4f4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4;padding:24px 0;">
<tr><td align="center">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:6px;overflow:hidden;">

  <tr><td style="background-color:#0a1f1a;padding:32px 36px;">
    <div style="font-size:22px;font-weight:700;color:#ffffff;">Strategy Agent</div>
    <div style="font-size:13px;color:#9bbfae;margin-top:4px;">Weekly Strategy, M&amp;A &amp; Markets Brief</div>
    <div style="font-size:12px;color:#6e8f7d;margin-top:12px;">{date_str} &middot; {total_items} stories &middot; ~30 min read</div>
  </td></tr>

  <tr><td style="padding:0 36px;">
    {sections}
  </td></tr>

  <tr><td style="padding:28px 36px;background-color:#fafafa;border-top:1px solid #eee;">
    <div style="font-size:12px;color:#999;line-height:1.6;">
      Sources are filtered by relevance to strategy, M&amp;A and markets, ordered South Africa &rarr; Africa &rarr; Global.
      Items already covered in a previous brief are automatically excluded.
      Analysis is generated and may contain errors &mdash; verify against the linked source before acting.
    </div>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""
