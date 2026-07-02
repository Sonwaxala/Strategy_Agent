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
    {"name": "BusinessTech", "url": "https://businesstech.co.za/news/feed/", "tier": "South Africa"},
    {"name": "Daily Maverick (Business Maverick)", "url": "https://www.dailymaverick.co.za/dmrss/", "tier": "South Africa"},
    {"name": "Mail & Guardian", "url": "https://mg.co.za/feed/", "tier": "South Africa"},
    {"name": "News24 Top Stories", "url": "https://feeds.news24.com/articles/news24/TopStories/rss", "tier": "South Africa"},
    {"name": "TechCentral", "url": "https://techcentral.co.za/feed", "tier": "South Africa"},

    # --- TIER 2: AFRICA ---
    {"name": "How We Made It In Africa", "url": "https://www.howwemadeitinafrica.com/feed/", "tier": "Africa"},
    {"name": "African Business Magazine", "url": "https://african.business/feed/", "tier": "Africa"},
    {"name": "The Africa Report", "url": "https://www.theafricareport.com/feed/", "tier": "Africa"},
    {"name": "AfricaBusiness.com", "url": "https://africabusiness.com/feed/", "tier": "Africa"},

    # --- TIER 3: GLOBAL ---
    {"name": "Reuters Business & Finance", "url": "https://www.reutersagency.com/feed/?best-topics=business-finance", "tier": "Global"},
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
