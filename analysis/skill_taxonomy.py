"""Skill taxonomy utilities for resolving aliases and categorizing skills."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Optional

from parsers.utils import load_skill_aliases, normalize_text


# Broad categories for grouping skills in the UI
SKILL_CATEGORIES = {
    "programming_languages": [
        "python", "javascript", "typescript", "java", "csharp", "cpp",
        "go", "rust", "ruby", "php", "swift", "kotlin", "scala", "r",
    ],
    "data_engineering": [
        "sql", "nosql", "spark", "hadoop", "airflow", "kafka", "dbt",
        "snowflake", "databricks", "etl", "redis", "elasticsearch",
    ],
    "machine_learning": [
        "machine_learning", "deep_learning", "nlp", "computer_vision",
        "llm", "rag", "tensorflow", "pytorch", "scikit_learn", "huggingface",
        "mlops", "ab_testing", "statistics",
    ],
    "data_tools": [
        "pandas", "numpy", "scipy", "data_visualization",
    ],
    "cloud_and_infra": [
        "aws", "gcp", "azure", "docker", "kubernetes", "terraform",
        "ci_cd", "linux",
    ],
    "web_development": [
        "react", "angular", "vue", "node", "django", "flask", "fastapi",
        "spring", "html_css", "rest_api", "graphql", "microservices",
    ],
    "general": [
        "git", "agile", "testing",
    ],
    "soft_skills": [
        "communication", "leadership", "problem_solving", "collaboration",
    ],
}


@lru_cache(maxsize=1)
def get_aliases() -> dict[str, list[str]]:
    """Cached loader for skill aliases."""
    return load_skill_aliases()


def get_category(skill: str) -> str:
    """Return the broad category a canonical skill belongs to."""
    for category, skills in SKILL_CATEGORIES.items():
        if skill in skills:
            return category
    return "other"


def categorize_skills(skills: list[str]) -> dict[str, list[str]]:
    """Group a list of canonical skills by category."""
    grouped: dict[str, list[str]] = {}
    for skill in skills:
        cat = get_category(skill)
        grouped.setdefault(cat, []).append(skill)
    return grouped


def resolve_alias(term: str) -> Optional[str]:
    """Given a raw term, return its canonical skill name or None."""
    aliases = get_aliases()
    normalized = normalize_text(term)
    for canonical, variants in aliases.items():
        for variant in variants:
            if len(variant) <= 3:
                pattern = rf"\b{re.escape(variant)}\b"
            else:
                pattern = rf"(?<!\w){re.escape(variant)}(?!\w)"
            if re.search(pattern, normalized):
                return canonical
    return None


def get_display_name(canonical: str) -> str:
    """Convert a canonical skill key to a human-readable name."""
    return canonical.replace("_", " ").title()
