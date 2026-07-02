"""
Sends collected articles to Claude for objective analysis and summarization.

"Not agreeable, but objective" is implemented directly in the prompt:
the model is instructed to assess strategic significance plainly, flag
risk/hype, and not perform enthusiasm it doesn't have evidence for.
"""

import json
import logging
import os

import anthropic

logger = logging.getLogger("strategy_agent.analyze")

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a strategy analyst producing a weekly intelligence brief for a \
business strategy professional. Your tone is objective and direct, not agreeable or \
promotional. You do not inflate the significance of minor news, and you do not soften \
genuinely significant developments. You call out when a deal, claim, or trend looks \
weak, overhyped, or under-substantiated by the source material, as readily as you \
highlight what is genuinely significant.

For each article provided, write a tight, information-dense summary (3-5 sentences) \
covering: what happened, the key parties involved, the strategic or financial \
rationale or impact, and — where relevant — your objective read on its significance \
(e.g. "minor regional deal, limited read-through" vs "signals a real shift in \
sector consolidation"). Do not editorialize beyond what the source material supports. \
Do not use marketing language ("game-changing", "exciting", "huge"). 

Return ONLY a JSON array, no preamble, no markdown fences. Each element:
{"title": "...", "url": "...", "source": "...", "tier": "...", "summary": "your analysis here"}

Preserve the title, url, source, and tier fields exactly as given in the input."""


def analyze(articles: list[dict]) -> list[dict]:
    """Takes raw articles, returns the same items with Claude-written
    objective summaries. Processes in batches to stay within reasonable
    token bounds."""
    if not articles:
        return []

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    batch_size = 12
    analyzed = []

    for i in range(0, len(articles), batch_size):
        batch = articles[i:i + batch_size]
        user_content = (
            "Analyze these articles for the weekly strategy brief. "
            "Input articles:\n\n" + json.dumps(batch, indent=2)
        )

        response = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )

        text = "".join(block.text for block in response.content if block.type == "text")
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        try:
            batch_result = json.loads(text)
            analyzed.extend(batch_result)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Claude response for batch %d: %s\nRaw: %s",
                         i // batch_size, e, text[:500])
            # Fall back to raw articles with a placeholder summary rather
            # than silently dropping the batch.
            for a in batch:
                a_copy = dict(a)
                a_copy["summary"] = a.get("summary", "")[:300] or "Summary unavailable — see full article."
                analyzed.append(a_copy)

    return analyzed
