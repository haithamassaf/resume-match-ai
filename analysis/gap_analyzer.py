"""Gap analysis between resume qualifications and job requirements."""

from __future__ import annotations

from typing import Optional

from analysis.skill_taxonomy import categorize_skills, get_display_name


def analyze_gaps(
    resume_skills: list[str],
    jd_required_skills: list[str],
    jd_preferred_skills: list[str],
    resume_years: list[dict],
    jd_years: list[dict],
    resume_education: list[str],
    jd_education: list[str],
    semantic_result: Optional[dict] = None,
) -> dict:
    """Comprehensive gap analysis between resume and JD.

    Combines hard skill gaps, experience gaps, education gaps, and
    semantic analysis (transferable skills) into a single report.

    Returns:
        dict with missing_required, missing_preferred, related_skills,
        experience_gap, education_gap, priority_gaps, and requirements_met_score.
    """
    resume_set = set(resume_skills)

    # --- Skill gaps ---
    missing_required = sorted(set(jd_required_skills) - resume_set)
    missing_preferred = sorted(set(jd_preferred_skills) - resume_set)
    matched_required = sorted(set(jd_required_skills) & resume_set)
    matched_preferred = sorted(set(jd_preferred_skills) & resume_set)

    # Find related skills: resume skills in the same category as missing ones
    related = _find_related_skills(resume_skills, missing_required + missing_preferred)

    # --- Experience gap ---
    experience_gap = _assess_experience_gap(resume_years, jd_years)

    # --- Education gap ---
    education_gap = _assess_education_gap(resume_education, jd_education)

    # --- Priority ranking of missing skills ---
    priority_gaps = _prioritize_gaps(
        missing_required, missing_preferred, experience_gap, education_gap
    )

    # --- Requirements met score (0-100) ---
    req_score = _compute_requirements_score(
        matched_required, jd_required_skills,
        matched_preferred, jd_preferred_skills,
        experience_gap, education_gap,
    )

    # --- Merge transferable skills from semantic analysis ---
    transferable = []
    if semantic_result and semantic_result.get("transferable_skills"):
        transferable = semantic_result["transferable_skills"]

    return {
        "missing_required": [get_display_name(s) for s in missing_required],
        "missing_required_keys": missing_required,
        "missing_preferred": [get_display_name(s) for s in missing_preferred],
        "missing_preferred_keys": missing_preferred,
        "matched_required": [get_display_name(s) for s in matched_required],
        "matched_preferred": [get_display_name(s) for s in matched_preferred],
        "related_skills": related,
        "transferable_skills": transferable,
        "experience_gap": experience_gap,
        "education_gap": education_gap,
        "priority_gaps": priority_gaps,
        "requirements_met_score": req_score,
    }


def _find_related_skills(
    resume_skills: list[str], missing_skills: list[str]
) -> list[dict]:
    """Find resume skills that are in the same category as missing skills."""
    if not missing_skills:
        return []

    resume_by_cat = categorize_skills(resume_skills)
    missing_by_cat = categorize_skills(missing_skills)
    related = []

    for cat, missing_in_cat in missing_by_cat.items():
        resume_in_cat = resume_by_cat.get(cat, [])
        if resume_in_cat:
            for m in missing_in_cat:
                related.append({
                    "missing": get_display_name(m),
                    "related_from_resume": [get_display_name(r) for r in resume_in_cat],
                    "category": cat.replace("_", " ").title(),
                })

    return related


def _assess_experience_gap(
    resume_years: list[dict], jd_years: list[dict]
) -> dict:
    """Compare years of experience between resume and JD."""
    jd_max = max((y["years"] for y in jd_years), default=0)
    resume_max = max((y["years"] for y in resume_years), default=0)

    if jd_max == 0:
        return {"status": "not_specified", "jd_requires": 0, "resume_has": resume_max}

    if resume_max >= jd_max:
        return {"status": "met", "jd_requires": jd_max, "resume_has": resume_max}
    elif resume_max >= jd_max - 1:
        return {"status": "close", "jd_requires": jd_max, "resume_has": resume_max}
    else:
        return {"status": "gap", "jd_requires": jd_max, "resume_has": resume_max}


def _assess_education_gap(
    resume_education: list[str], jd_education: list[str]
) -> dict:
    """Simple education requirement check."""
    if not jd_education:
        return {"status": "not_specified", "jd_requires": [], "resume_has": resume_education}

    # Rough degree level ordering for comparison
    degree_levels = {"bachelor": 1, "b.s": 1, "b.a": 1, "master": 2, "m.s": 2, "m.a": 2, "mba": 2, "ph.d": 3, "doctorate": 3}

    jd_level = 0
    for edu in jd_education:
        for key, level in degree_levels.items():
            if key in edu.lower():
                jd_level = max(jd_level, level)

    resume_level = 0
    for edu in resume_education:
        for key, level in degree_levels.items():
            if key in edu.lower():
                resume_level = max(resume_level, level)

    if resume_level >= jd_level:
        status = "met"
    elif resume_level > 0:
        status = "partial"
    else:
        status = "unknown"  # Can't determine from parsed text

    return {
        "status": status,
        "jd_requires": jd_education,
        "resume_has": resume_education,
    }


def _prioritize_gaps(
    missing_required: list[str],
    missing_preferred: list[str],
    experience_gap: dict,
    education_gap: dict,
) -> list[dict]:
    """Rank gaps by priority for the user to address."""
    gaps = []

    # Experience gap is high priority
    if experience_gap.get("status") == "gap":
        gaps.append({
            "type": "experience",
            "priority": "high",
            "description": (
                f"JD requires {experience_gap['jd_requires']}+ years, "
                f"resume shows ~{experience_gap['resume_has']} years"
            ),
        })

    # Missing required skills are high priority
    for skill in missing_required:
        gaps.append({
            "type": "required_skill",
            "priority": "high",
            "description": f"Missing required skill: {get_display_name(skill)}",
            "skill": skill,
        })

    # Education gap is medium priority
    if education_gap.get("status") == "partial":
        gaps.append({
            "type": "education",
            "priority": "medium",
            "description": "Education level may not fully meet requirements",
        })

    # Missing preferred skills are lower priority
    for skill in missing_preferred:
        gaps.append({
            "type": "preferred_skill",
            "priority": "low",
            "description": f"Missing preferred skill: {get_display_name(skill)}",
            "skill": skill,
        })

    return gaps


def _compute_requirements_score(
    matched_required: list[str],
    jd_required: list[str],
    matched_preferred: list[str],
    jd_preferred: list[str],
    experience_gap: dict,
    education_gap: dict,
) -> float:
    """Compute a 0-100 score for how well requirements are met.

    Weights:
    - Required skills: 50%
    - Preferred skills: 15%
    - Experience: 20%
    - Education: 15%
    """
    # Required skills ratio
    req_ratio = len(matched_required) / len(jd_required) if jd_required else 1.0

    # Preferred skills ratio
    pref_ratio = len(matched_preferred) / len(jd_preferred) if jd_preferred else 1.0

    # Experience score
    exp_status = experience_gap.get("status", "not_specified")
    exp_scores = {"met": 1.0, "close": 0.75, "not_specified": 1.0, "gap": 0.3}
    exp_score = exp_scores.get(exp_status, 0.5)

    # Education score
    edu_status = education_gap.get("status", "not_specified")
    edu_scores = {"met": 1.0, "partial": 0.6, "not_specified": 1.0, "unknown": 0.8}
    edu_score = edu_scores.get(edu_status, 0.5)

    raw = (
        req_ratio * 0.50
        + pref_ratio * 0.15
        + exp_score * 0.20
        + edu_score * 0.15
    )
    return round(raw * 100, 1)
