"""Centralized prompt templates for all Claude API calls."""

BULLET_REWRITE_PROMPT = """\
You are a resume optimization expert. Rewrite the following resume bullet \
point to better align with this job description.

Rules:
- Keep the same underlying experience and facts
- Do NOT fabricate achievements or inflate numbers
- Incorporate relevant keywords from the job description naturally
- Use strong action verbs
- Quantify impact where the original already has numbers
- Keep it to 1-2 lines max
- Do not use em dashes

Original bullet: {bullet}
Job description context: {jd_context}

Respond with ONLY the rewritten bullet, nothing else."""

BATCH_REWRITE_PROMPT = """\
You are a resume optimization expert. Rewrite each of the following resume \
bullet points to better align with the target job description.

Rules:
- Keep the same underlying experience and facts for each bullet
- Do NOT fabricate achievements or inflate numbers
- Incorporate relevant keywords from the job description naturally
- Use strong action verbs
- Quantify impact where the original already has numbers
- Keep each bullet to 1-2 lines max
- Do not use em dashes

Job description:
{jd_context}

Original bullets:
{numbered_bullets}

Respond in JSON (no markdown fences):
{{
  "rewrites": [
    {{"original": "...", "rewritten": "..."}},
    ...
  ]
}}"""

VALIDATION_PROMPT = """\
You are a fact-checking assistant. Compare the original and rewritten resume \
bullet points below. Determine whether the rewrite is faithful to the original.

Flag the rewrite if it:
1. Adds accomplishments, metrics, or results NOT present in the original
2. Claims use of technologies or tools NOT mentioned or implied in the original
3. Inflates scope (e.g., "team" becomes "organization-wide")
4. Changes the core meaning of what was done

Original: {original}
Rewritten: {rewritten}

Respond in JSON (no markdown fences):
{{
  "is_faithful": true/false,
  "issues": ["...", "..."],
  "severity": "none" | "minor" | "major"
}}"""
