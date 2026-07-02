# Strategy Agent

A weekly automated brief covering Strategy, M&A, and Markets news, ordered
South Africa → Africa → Global. Runs every Monday 09:30 SAST via GitHub
Actions and emails the report to sonwabo@edpartner.co.za.

## How it actually runs (read this first)

This does **not** run on your computer, and it does not "launch when your
computer starts." That would mean a missed Monday if your laptop is off
or asleep — not acceptable for a weekly delivery commitment. Instead it
runs on GitHub's servers via GitHub Actions, on a cron schedule,
completely independent of any device being on. That is the "always
connected" version of this requirement that's actually reliable.

## What's in this repo

| File | Purpose |
|---|---|
| `feeds.py` | The 14 RSS sources, tiered SA → Africa → Global, plus relevance keywords |
| `ingest.py` | Fetches feeds, filters by relevance + recency, drops anything already sent |
| `memory.py` | SQLite-backed dedup store — tracks every article ever sent by URL and a normalized title fingerprint, so the same story from a different outlet is still caught |
| `analyze.py` | Sends filtered articles to Claude for objective, non-promotional summarization |
| `report.py` | Builds the clean HTML report, grouped by tier |
| `deliver.py` | Sends the report via Gmail SMTP |
| `main.py` | Orchestrates the full pipeline |
| `.github/workflows/weekly_report.yml` | The actual Monday 09:30 SAST scheduler |

## One-time setup (you need to do this — I can't click your accounts for you)

### 1. Create the GitHub repo
```bash
cd strategy-agent
git init
git add .
git commit -m "Initial Strategy Agent"
git remote add origin https://github.com/<your-username>/strategy-agent.git
git push -u origin main
```

### 2. Get an Anthropic API key
Go to console.anthropic.com → API Keys → create one. This is **separate**
from your claude.ai login.

### 3. Get a Gmail App Password (not your normal Gmail password)
Gmail blocks plain-password SMTP. You need an App Password:
1. Go to myaccount.google.com/security
2. Turn on 2-Step Verification if it isn't already on (required for App Passwords)
3. Go to myaccount.google.com/apppasswords
4. Generate one for "Mail" — copy the 16-character password

### 4. Add three secrets to the GitHub repo
In your repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | your Anthropic API key |
| `GMAIL_ADDRESS` | the Gmail address you'll send *from* |
| `GMAIL_APP_PASSWORD` | the 16-character App Password from step 3 |

### 5. Confirm Actions is enabled
Repo → **Actions** tab → if prompted, click "I understand my workflows, enable them."

### 6. Test it before trusting Monday
Repo → **Actions** → "Strategy Agent Weekly Report" → **Run workflow**
(this is the `workflow_dispatch` trigger — runs it immediately, doesn't
wait for Monday). Check sonwabo@edpartner.co.za and the Actions log.

## Verifying / maintaining the feed list

RSS feed URLs occasionally move or get rate-limited by publishers. If a
feed in `feeds.py` starts consistently returning 0 entries (visible in
the Actions log), check the publication's site for `/feed` or `/rss` and
update the URL. The agent skips a dead feed with a warning rather than
failing the whole run, but a dead feed silently means less coverage —
worth a periodic glance at the logs.

## On "not agreeable, but objective"

This is implemented in `analyze.py`'s system prompt: Claude is instructed
to assess strategic significance plainly, call out weak or overhyped
claims as readily as genuine significance, and avoid promotional
language. If you find the tone drifting either too critical or too soft
over time, that prompt is the place to adjust it.

## On deduplication

Per your spec, "must not repeat information already shared" is checked
against the **full history** of everything ever sent (not just last
week), via two methods: exact URL match, and a normalized-title
fingerprint that catches the same story re-reported by a different
outlet under a different URL. The dedup database (`strategy_agent_memory.db`)
is committed back to the repo after every run, so this memory persists
indefinitely across weeks.

## Local testing
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export GMAIL_ADDRESS=you@gmail.com
export GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx
python main.py
```
