"""Weighted composite scorer combining keyword, semantic, and requirements scores."""

from config.settings import KEYWORD_WEIGHT, REQUIREMENTS_WEIGHT, SEMANTIC_WEIGHT


def compute_overall_score(
    keyword_score: float,
    semantic_score: float,
    requirements_score: float,
) -> dict:
    """Compute the weighted overall match score.

    Default weights from settings:
    - Keyword match: 30%
    - Semantic match: 40%
    - Requirements met: 30%

    All input scores should be 0-100. Returns the composite score
    and a breakdown of each component's contribution.
    """
    weighted_keyword = keyword_score * KEYWORD_WEIGHT
    weighted_semantic = semantic_score * SEMANTIC_WEIGHT
    weighted_requirements = requirements_score * REQUIREMENTS_WEIGHT

    overall = weighted_keyword + weighted_semantic + weighted_requirements
    overall = round(max(0, min(100, overall)), 1)

    return {
        "overall_score": overall,
        "breakdown": {
            "keyword": {
                "score": round(keyword_score, 1),
                "weight": KEYWORD_WEIGHT,
                "contribution": round(weighted_keyword, 1),
            },
            "semantic": {
                "score": round(semantic_score, 1),
                "weight": SEMANTIC_WEIGHT,
                "contribution": round(weighted_semantic, 1),
            },
            "requirements": {
                "score": round(requirements_score, 1),
                "weight": REQUIREMENTS_WEIGHT,
                "contribution": round(weighted_requirements, 1),
            },
        },
        "grade": _score_to_grade(overall),
        "summary": _score_to_summary(overall),
    }


def _score_to_grade(score: float) -> str:
    """Convert a numeric score to a letter grade."""
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B+"
    elif score >= 60:
        return "B"
    elif score >= 50:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"


def _score_to_summary(score: float) -> str:
    """Generate a one-line summary based on score."""
    if score >= 85:
        return "Excellent match -- you're a strong candidate for this role."
    elif score >= 70:
        return "Good match -- you meet most requirements with some gaps to address."
    elif score >= 55:
        return "Moderate match -- several key areas need strengthening."
    elif score >= 40:
        return "Weak match -- significant gaps between your profile and the requirements."
    else:
        return "Low match -- this role may require skills outside your current experience."


def run_full_analysis(
    resume_text: str,
    jd_text: str,
    resume_skills: list[str],
    jd_data: dict,
    use_semantic: bool = True,
) -> dict:
    """Run the complete analysis pipeline and return all results.

    Args:
        resume_text: Full resume text.
        jd_text: Full job description text.
        resume_skills: Canonical skill names from resume.
        jd_data: Parsed JD dict from job_parser.parse_job_description().
        use_semantic: Whether to call Claude API for semantic analysis.

    Returns:
        dict with overall_score, keyword_result, semantic_result,
        gap_result, and score_breakdown.
    """
    from analysis.gap_analyzer import analyze_gaps
    from analysis.keyword_matcher import compute_keyword_score
    from analysis.semantic_matcher import compute_semantic_score

    # 1. Keyword matching
    keyword_result = compute_keyword_score(
        resume_text=resume_text,
        jd_text=jd_text,
        resume_skills=resume_skills,
        jd_required_skills=jd_data["required_skills"],
        jd_preferred_skills=jd_data["preferred_skills"],
    )

    # 2. Semantic matching (optional -- requires API key)
    if use_semantic:
        semantic_result = compute_semantic_score(resume_text, jd_text)
    else:
        semantic_result = {
            "score": 0,
            "strengths": [],
            "gaps": [],
            "transferable_skills": [],
            "reasoning": "Semantic analysis skipped.",
        }

    # 3. Gap analysis
    gap_result = analyze_gaps(
        resume_skills=resume_skills,
        jd_required_skills=jd_data["required_skills"],
        jd_preferred_skills=jd_data["preferred_skills"],
        resume_years=jd_data.get("years_of_experience", []),
        jd_years=jd_data.get("years_of_experience", []),
        resume_education=[],  # Populated when parsing PDF resume
        jd_education=jd_data.get("education", []),
        semantic_result=semantic_result,
    )

    # 4. Composite score
    score_result = compute_overall_score(
        keyword_score=keyword_result["score"],
        semantic_score=semantic_result["score"],
        requirements_score=gap_result["requirements_met_score"],
    )

    return {
        "overall": score_result,
        "keyword": keyword_result,
        "semantic": semantic_result,
        "gaps": gap_result,
    }
