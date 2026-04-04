"""Keyword matching using TF-IDF similarity and alias-aware exact matching."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from analysis.skill_taxonomy import categorize_skills, get_display_name
from parsers.utils import normalize_text


def compute_tfidf_similarity(resume_text: str, jd_text: str) -> float:
    """Compute TF-IDF cosine similarity between resume and JD text.

    Returns a score from 0.0 to 1.0.
    """
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=5000,
    )
    tfidf_matrix = vectorizer.fit_transform([
        normalize_text(resume_text),
        normalize_text(jd_text),
    ])
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return float(similarity[0][0])


def compute_skill_overlap(
    resume_skills: list[str], jd_skills: list[str]
) -> dict:
    """Compare resume skills against JD skills using canonical names.

    Returns detailed overlap analysis with matched, missing, and extra skills.
    """
    resume_set = set(resume_skills)
    jd_set = set(jd_skills)

    matched = sorted(resume_set & jd_set)
    missing = sorted(jd_set - resume_set)
    extra = sorted(resume_set - jd_set)

    total_jd = len(jd_set)
    overlap_ratio = len(matched) / total_jd if total_jd > 0 else 0.0

    return {
        "matched": matched,
        "missing": missing,
        "extra": extra,
        "matched_display": [get_display_name(s) for s in matched],
        "missing_display": [get_display_name(s) for s in missing],
        "extra_display": [get_display_name(s) for s in extra],
        "overlap_ratio": overlap_ratio,
        "matched_count": len(matched),
        "missing_count": len(missing),
        "total_jd_skills": total_jd,
    }


def compute_categorized_overlap(
    resume_skills: list[str], jd_skills: list[str]
) -> dict[str, dict]:
    """Break down skill overlap by category (e.g. programming, ML, cloud)."""
    resume_by_cat = categorize_skills(resume_skills)
    jd_by_cat = categorize_skills(jd_skills)

    all_categories = set(list(resume_by_cat.keys()) + list(jd_by_cat.keys()))
    breakdown = {}

    for cat in sorted(all_categories):
        r_skills = set(resume_by_cat.get(cat, []))
        j_skills = set(jd_by_cat.get(cat, []))
        matched = sorted(r_skills & j_skills)
        missing = sorted(j_skills - r_skills)

        breakdown[cat] = {
            "matched": [get_display_name(s) for s in matched],
            "missing": [get_display_name(s) for s in missing],
            "score": len(matched) / len(j_skills) if j_skills else 1.0,
        }

    return breakdown


def compute_keyword_score(
    resume_text: str,
    jd_text: str,
    resume_skills: list[str],
    jd_required_skills: list[str],
    jd_preferred_skills: list[str],
) -> dict:
    """Compute the overall keyword match score (0-100).

    Combines:
    - TF-IDF text similarity (30% of keyword score)
    - Required skill overlap (50% of keyword score)
    - Preferred skill overlap (20% of keyword score)
    """
    tfidf_score = compute_tfidf_similarity(resume_text, jd_text)

    all_jd_skills = list(set(jd_required_skills + jd_preferred_skills))
    skill_overlap = compute_skill_overlap(resume_skills, all_jd_skills)
    category_breakdown = compute_categorized_overlap(resume_skills, all_jd_skills)

    # Required skill match rate
    required_set = set(jd_required_skills)
    resume_set = set(resume_skills)
    required_matched = required_set & resume_set
    required_ratio = len(required_matched) / len(required_set) if required_set else 1.0

    # Preferred skill match rate
    preferred_set = set(jd_preferred_skills)
    preferred_matched = preferred_set & resume_set
    preferred_ratio = len(preferred_matched) / len(preferred_set) if preferred_set else 1.0

    # Weighted keyword score
    raw_score = (
        tfidf_score * 0.30
        + required_ratio * 0.50
        + preferred_ratio * 0.20
    )
    score = round(raw_score * 100, 1)

    return {
        "score": score,
        "tfidf_similarity": round(tfidf_score, 4),
        "required_match_rate": round(required_ratio, 4),
        "preferred_match_rate": round(preferred_ratio, 4),
        "skill_overlap": skill_overlap,
        "category_breakdown": category_breakdown,
    }
