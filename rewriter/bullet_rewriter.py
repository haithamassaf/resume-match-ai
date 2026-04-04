"""Claude API-powered bullet point rewriter for resume optimization."""

from __future__ import annotations

import json

import anthropic

from config.settings import ANTHROPIC_API_KEY, CLAUDE_MODEL
from rewriter.prompts import BATCH_REWRITE_PROMPT, BULLET_REWRITE_PROMPT


def rewrite_bullet(bullet: str, jd_context: str) -> dict:
    """Rewrite a single resume bullet point to align with a job description.

    Args:
        bullet: Original resume bullet text.
        jd_context: Relevant job description text (responsibilities + requirements).

    Returns:
        dict with original, rewritten, and error (if any).
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = BULLET_REWRITE_PROMPT.format(
        bullet=bullet,
        jd_context=_truncate(jd_context, 2000),
    )

    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        rewritten = message.content[0].text.strip()
        # Clean up any surrounding quotes the model might add
        if rewritten.startswith('"') and rewritten.endswith('"'):
            rewritten = rewritten[1:-1]
        # Strip leading bullet marker if model re-added one
        rewritten = rewritten.lstrip("•-▪► ").strip()

        return {"original": bullet, "rewritten": rewritten}

    except anthropic.APIError as e:
        return {"original": bullet, "rewritten": bullet, "error": str(e)}


def rewrite_bullets_batch(bullets: list[str], jd_context: str) -> list[dict]:
    """Rewrite multiple bullets in a single API call for efficiency.

    Falls back to one-by-one rewriting if the batch call fails to parse.

    Args:
        bullets: List of original resume bullet texts.
        jd_context: Full job description or relevant sections.

    Returns:
        List of dicts, each with original and rewritten text.
    """
    if not bullets:
        return []

    # For small lists, just do individual calls
    if len(bullets) <= 2:
        return [rewrite_bullet(b, jd_context) for b in bullets]

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    numbered = "\n".join(f"{i+1}. {b}" for i, b in enumerate(bullets))
    prompt = BATCH_REWRITE_PROMPT.format(
        jd_context=_truncate(jd_context, 2000),
        numbered_bullets=numbered,
    )

    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1]
            response_text = response_text.rsplit("```", 1)[0]

        data = json.loads(response_text)
        rewrites = data.get("rewrites", [])

        # Align results back to original bullets
        results = []
        for i, bullet in enumerate(bullets):
            if i < len(rewrites):
                rewritten = rewrites[i].get("rewritten", bullet)
                rewritten = rewritten.lstrip("•-▪► ").strip()
                results.append({"original": bullet, "rewritten": rewritten})
            else:
                results.append({"original": bullet, "rewritten": bullet, "error": "Missing from batch response"})

        return results

    except (anthropic.APIError, json.JSONDecodeError, KeyError):
        # Fallback: rewrite one by one
        return [rewrite_bullet(b, jd_context) for b in bullets]


def build_jd_context(jd_data: dict) -> str:
    """Build a concise JD context string from parsed job description data.

    Combines responsibilities and requirements into a focused context
    for the rewriter prompt.
    """
    parts = []

    sections = jd_data.get("sections", {})
    if "responsibilities" in sections:
        parts.append("Key Responsibilities:\n" + sections["responsibilities"])
    if "required" in sections:
        parts.append("Required Qualifications:\n" + sections["required"])
    if "preferred" in sections:
        parts.append("Preferred Qualifications:\n" + sections["preferred"])

    if parts:
        return "\n\n".join(parts)

    # Fallback to raw text
    return jd_data.get("raw_text", "")


def _truncate(text: str, max_chars: int) -> str:
    """Truncate text to max_chars at a word boundary."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.8:
        truncated = truncated[:last_space]
    return truncated + "..."
