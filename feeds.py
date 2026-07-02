"""
Feed configuration for the Strategy Agent.

Tiers determine presentation order in the report: South Africa first,
then Africa, then Global. Within a tier, feeds are processed in listed order.

NOTE: Feed URLs occasionally change or get rate-limited. If a feed starts
returning 0 entries or errors consistently, check the publication's site
for /feed or /rss and update the URL here. The agent will skip a dead feed
and log a warning rather than failing the whole run.
"""

FEEDS = [
    # --- TIER 1: SOUTH AFRICA ---
    {"name": "Moneyweb", "url": "https://www.moneyweb.co.za/feed/", "tier": "South Africa"},

    # BusinessTech native feed had malformed XML. Google News RSS for the
    # site is cleaner and updated just as fast.
    {"name": "BusinessTech", "url": "https://news.google.com/rss/search?q=site:businesstech.co.za&hl=en-ZA&gl=ZA&ceid=ZA:en", "tier": "South Africa"},

    {"name": "Daily Maverick (Business Maverick)", "url": "https://www.dailymaverick.co.za/dmrss/", "tier": "South Africa"},

    # Mail & Guardian native feed had malformed XML. Google News RSS fallback.
    {"name": "Mail & Guardian", "url": "https://news.google.com/rss/search?q=site:mg.co.za&hl=en-ZA&gl=ZA&ceid=ZA:en", "tier": "South Africa"},

    # Old feeds.news24.com subdomain is dead (DNS failure). Correct current
    # URL is through the capi24 API — using Fin24 (News24's business section)
    # which is the most relevant for this brief.
    {"name": "News24 / Fin24 (Business)", "url": "https://feeds.capi24.com/v1/Search/articles/news24/fin24/rss", "tier": "South Africa"},

    {"name": "TechCentral", "url": "https://techcentral.co.za/feed", "tier": "South Africa"},

    # --- TIER 2: AFRICA ---
    {"name": "How We Made It In Africa", "url": "https://www.howwemadeitinafrica.com/feed/", "tier": "Africa"},
    {"name": "African Business Magazine", "url": "https://african.business/feed/", "tier": "Africa"},
    {"name": "The Africa Report", "url": "https://www.theafricareport.com/feed/", "tier": "Africa"},

    # AfricaBusiness.com had a mismatched tag (broken XML). Replaced with
    # Ventures Africa which covers the same beat and has a clean feed.
    {"name": "Ventures Africa", "url": "https://venturesafrica.com/feed/", "tier": "Africa"},

    # --- TIER 3: GLOBAL ---
    # Reuters agency feed was broken. Using Google News RSS for Reuters
    # business coverage — reliable and self-updating.
    {"name": "Reuters (via Google News)", "url": "https://news.google.com/rss/search?q=reuters+mergers+acquisitions+strategy&hl=en&gl=US&ceid=US:en", "tier": "Global"},

    # FT RSS requires a subscription to render content. Kept in as it
    # returns headlines even without full-text access.
    {"name": "Financial Times (Companies)", "url": "https://www.ft.com/companies?format=rss", "tier": "Global"},

    {"name": "Fortune", "url": "https://fortune.com/feed/", "tier": "Global"},
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/news/rssindex", "tier": "Global"},
]

TIER_ORDER = ["South Africa", "Africa", "Global"]

# Keywords used to score relevance to "Strategy, M&A, and Markets" before
# items are sent to Claude for analysis. This keeps noisy general-news
# feeds (News24, Daily Maverick) focused on the brief.
RELEVANCE_KEYWORDS = [
    "merger", "acquisition", "acquire", "acquires", "acquired", "takeover",
    "buyout", "deal", "stake", "shares", "valuation", "ipo", "listing",
    "delisting", "strategy", "strategic", "restructur", "joint venture",
    "partnership", "investment", "investor", "funding", "capital raise",
    "private equity", "venture capital", "divest", "spin-off", "spinoff",
    "consolidation", "expansion", "market share", "competitor", "ceo",
    "board", "earnings", "results", "outlook", "forecast", "regulator",
    "antitrust", "competition commission", "jse", "nasdaq", "nyse",
    "billion", "million", "rand", "dollar", "growth", "decline", "sale of",
]
