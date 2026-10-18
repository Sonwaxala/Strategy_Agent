"""
Sends collected articles to Claude for objective analysis and summarization.

"Not agreeable, but objective" is implemented directly in the prompt:
the model is instructed to assess strategic significance plainly, flag
risk/hype, and not perform enthusiasm it doesn't have evidence for.

Claude is called through the Claude Code CLI (`claude -p`) rather than the
Anthropic API SDK, so usage is covered by the Claude subscription tied to
CLAUDE_CODE_OAUTH_TOKEN instead of pay-as-you-go API credits.
"""

import json
import logging
import os
import shutil
import subprocess
import tempfile

logger = logging.getLogger("strategy_agent.analyze")

# A Claude Code model alias ("sonnet", "opus", "haiku") or a full model name.
MODEL = os.environ.get("STRATEGY_AGENT_MODEL", "sonnet")

# Seconds to wait for one batch before giving up.
BATCH_TIMEOUT = 300

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


class ClaudeCallError(RuntimeError):
    """Raised when the Claude Code CLI is missing, unauthenticated, or fails."""


def _check_setup() -> str:
    """Returns the path to the claude binary, or raises with a clear message."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        raise ClaudeCallError(
            "Claude Code CLI not found on PATH. Install it with "
            "`npm install -g @anthropic-ai/claude-code`."
        )
    if not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        raise ClaudeCallError(
            "CLAUDE_CODE_OAUTH_TOKEN is not set. Generate one with "
            "`claude setup-token` and add it as a GitHub Actions secret."
        )
    return claude_bin


def _call_claude(claude_bin: str, user_content: str) -> str:
    """Runs one prompt through `claude -p` and returns the reply text."""
    # In -p mode an API key in the environment always wins over the
    # subscription token, which would send this straight back to API billing.
    env = {
        k: v for k, v in os.environ.items()
        if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
    }

    cmd = [
        claude_bin,
        "-p",                          # non-interactive; prompt comes from stdin
        "--model", MODEL,
        "--system-prompt", SYSTEM_PROMPT,   # replace Claude Code's coding prompt
        "--tools", "",                 # pure text task: no file or shell tools
        "--strict-mcp-config",         # no MCP servers
        "--no-session-persistence",    # nothing saved to disk
        "--output-format", "json",
    ]

    # Run from an empty directory so nothing in the repo (CLAUDE.md, settings,
    # .mcp.json) leaks into the prompt.
    with tempfile.TemporaryDirectory() as workdir:
        try:
            proc = subprocess.run(
                cmd,
                input=user_content,
                capture_output=True,
                text=True,
                timeout=BATCH_TIMEOUT,
                env=env,
                cwd=workdir,
            )
        except subprocess.TimeoutExpired as e:
            raise ClaudeCallError(
                f"Claude Code timed out after {BATCH_TIMEOUT}s"
            ) from e

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise ClaudeCallError(
            f"Claude Code exited with code {proc.returncode} and no readable "
            f"result. stdout: {proc.stdout[:500]!r} stderr: {proc.stderr[:500]!r}"
        ) from None

    # Some versions emit a list of events; the final "result" event is the one we want.
    if isinstance(payload, list):
        results = [p for p in payload if isinstance(p, dict) and p.get("type") == "result"]
        payload = results[-1] if results else {}

    result = payload.get("result") or ""
    if proc.returncode != 0 or payload.get("is_error"):
        # Covers an expired/invalid token and hitting the plan's usage limit.
        raise ClaudeCallError(
            f"Claude Code call failed (exit code {proc.returncode}): "
            f"{result[:500] or proc.stderr[:500]}"
        )
    return result


def analyze(articles: list[dict]) -> list[dict]:
    """Takes raw articles, returns the same items with Claude-written
    objective summaries. Processes in batches to stay within reasonable
    token bounds."""
    if not articles:
        return []

    claude_bin = _check_setup()

    batch_size = 12
    analyzed = []

    for i in range(0, len(articles), batch_size):
        batch = articles[i:i + batch_size]
        user_content = (
            "Analyze these articles for the weekly strategy brief. "
            "Input articles:\n\n" + json.dumps(batch, indent=2)
        )

        text = _call_claude(claude_bin, user_content).strip()
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
