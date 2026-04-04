"""Validation layer to ensure bullet rewrites stay truthful."""

from __future__ import annotations

import json
import re

import anthropic

from config.settings import ANTHROPIC_API_KEY, CLAUDE_MODEL
from rewriter.prompts import VALIDATION_PROMPT


def validate_rewrite(original: str, rewritten: str) -> dict:
    """Use Claude API to check if a rewrite is faithful to the original.

    Returns:
        dict with is_faithful (bool), issues (list), severity (str).
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = VALIDATION_PROMPT.format(original=original, rewritten=rewritten)

    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1]
            response_text = response_text.rsplit("```", 1)[0]

        result = json.loads(response_text)
        result.setdefault("is_faithful", True)
        result.setdefault("issues", [])
        result.setdefault("severity", "none")
        return result

    except (anthropic.APIError, json.JSONDecodeError):
        # If API validation fails, fall back to local heuristics
        return validate_rewrite_local(original, rewritten)


def validate_rewrite_local(original: str, rewritten: str) -> dict:
    """Fast local heuristic checks for rewrite faithfulness.

    Catches the most common fabrication patterns without an API call.
    """
    issues = []

    # Check for fabricated numbers
    original_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", original))
    rewritten_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", rewritten))
    new_numbers = rewritten_numbers - original_numbers
    if new_numbers:
        issues.append(f"New numbers added that weren't in original: {', '.join(new_numbers)}")

    # Check for fabricated dollar amounts
    original_dollars = set(re.findall(r"\$[\d,.]+[KMBkmb]?", original))
    rewritten_dollars = set(re.findall(r"\$[\d,.]+[KMBkmb]?", rewritten))
    new_dollars = rewritten_dollars - original_dollars
    if new_dollars:
        issues.append(f"New dollar amounts added: {', '.join(new_dollars)}")

    # Check for scope inflation keywords
    inflation_phrases = [
        "company-wide", "organization-wide", "enterprise-wide",
        "across the organization", "across the company",
        "division-wide", "globally",
    ]
    orig_lower = original.lower()
    rewrite_lower = rewritten.lower()
    for phrase in inflation_phrases:
        if phrase in rewrite_lower and phrase not in orig_lower:
            issues.append(f"Possible scope inflation: '{phrase}' added")

    # Check for excessive length increase (more than 2x)
    if len(rewritten) > len(original) * 2.5:
        issues.append("Rewrite is significantly longer than original")

    # Determine severity
    if not issues:
        severity = "none"
    elif any("number" in i.lower() or "dollar" in i.lower() for i in issues):
        severity = "major"
    else:
        severity = "minor"

    return {
        "is_faithful": len(issues) == 0,
        "issues": issues,
        "severity": severity,
    }


def validate_batch(rewrites: list[dict], use_api: bool = False) -> list[dict]:
    """Validate a batch of rewrites, adding validation results to each.

    Args:
        rewrites: List of dicts with 'original' and 'rewritten' keys.
        use_api: If True, use Claude API for validation. Otherwise, use local heuristics.

    Returns:
        The same list with a 'validation' key added to each dict.
    """
    validate_fn = validate_rewrite if use_api else validate_rewrite_local

    for item in rewrites:
        if item.get("error"):
            item["validation"] = {
                "is_faithful": True,
                "issues": [],
                "severity": "none",
                "note": "Skipped -- rewrite failed",
            }
        else:
            item["validation"] = validate_fn(item["original"], item["rewritten"])

    return rewrites
