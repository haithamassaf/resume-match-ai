"""Semantic matching using Claude API for deep resume-JD analysis."""

import json

import anthropic

from config.settings import ANTHROPIC_API_KEY, CLAUDE_MODEL

SEMANTIC_MATCH_PROMPT = """\
You are an expert technical recruiter analyzing resume-job fit.

Given this resume text and job description, analyze:
1. How well does the candidate's experience align with the job responsibilities?
2. Are there transferable skills not captured by simple keyword matching?
3. What specific experiences demonstrate readiness for this role?
4. What are the biggest gaps between the candidate and the ideal applicant?

Score the semantic fit from 0-100 and explain your reasoning.

Resume:
{resume_text}

Job Description:
{jd_text}

Respond in JSON (no markdown fences):
{{
  "score": <0-100>,
  "strengths": ["...", "..."],
  "gaps": ["...", "..."],
  "transferable_skills": ["...", "..."],
  "reasoning": "..."
}}"""


def compute_semantic_score(resume_text: str, jd_text: str) -> dict:
    """Use Claude API to analyze semantic fit between resume and JD.

    Returns:
        dict with score (0-100), strengths, gaps, transferable_skills, reasoning.
        On API failure, returns a fallback dict with score=0 and error info.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = SEMANTIC_MATCH_PROMPT.format(
        resume_text=_truncate(resume_text, 6000),
        jd_text=_truncate(jd_text, 3000),
    )

    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text.strip()
        # Handle potential markdown fences in response
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1]
            response_text = response_text.rsplit("```", 1)[0]

        result = json.loads(response_text)

        # Validate and clamp score
        result["score"] = max(0, min(100, int(result.get("score", 0))))
        result.setdefault("strengths", [])
        result.setdefault("gaps", [])
        result.setdefault("transferable_skills", [])
        result.setdefault("reasoning", "")

        return result

    except anthropic.APIError as e:
        return _fallback_result(f"Claude API error: {e}")
    except (json.JSONDecodeError, KeyError) as e:
        return _fallback_result(f"Failed to parse Claude response: {e}")


def _truncate(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, cutting at the last word boundary."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.8:
        truncated = truncated[:last_space]
    return truncated + "..."


def _fallback_result(error_msg: str) -> dict:
    """Return a zero-score result when API call fails."""
    return {
        "score": 0,
        "strengths": [],
        "gaps": [],
        "transferable_skills": [],
        "reasoning": f"Semantic analysis unavailable: {error_msg}",
        "error": error_msg,
    }
