"""Export / download tailored resume content."""

import json
from datetime import datetime

import streamlit as st


def render_export_section(
    analysis_result: dict,
    rewrites: list,
    resume_skills: list,
):
    """Render download buttons for analysis results and rewritten bullets."""
    col1, col2 = st.columns(2)

    with col1:
        # -- Download rewritten bullets as plain text --
        if rewrites:
            bullet_lines = []
            for item in rewrites:
                if not item.get("error") and item.get("validation", {}).get("is_faithful", True):
                    bullet_lines.append(f"- {item['rewritten']}")
                else:
                    bullet_lines.append(f"- {item['original']}  [unchanged]")

            bullets_text = "\n".join(bullet_lines)
            st.download_button(
                label="Download Rewritten Bullets",
                data=bullets_text,
                file_name="tailored_bullets.txt",
                mime="text/plain",
            )

    with col2:
        # -- Download full analysis report as JSON --
        report = _build_report(analysis_result, rewrites, resume_skills)
        report_json = json.dumps(report, indent=2)
        st.download_button(
            label="Download Full Report (JSON)",
            data=report_json,
            file_name="match_report.json",
            mime="application/json",
        )


def _build_report(
    analysis_result: dict,
    rewrites: list,
    resume_skills: list,
) -> dict:
    """Build a structured report dict for export."""
    overall = analysis_result.get("overall", {})
    keyword = analysis_result.get("keyword", {})
    gaps = analysis_result.get("gaps", {})
    semantic = analysis_result.get("semantic", {})

    return {
        "generated_at": datetime.now().isoformat(),
        "match_score": overall.get("overall_score"),
        "grade": overall.get("grade"),
        "summary": overall.get("summary"),
        "score_breakdown": overall.get("breakdown"),
        "resume_skills": resume_skills,
        "matched_skills": keyword.get("skill_overlap", {}).get("matched_display", []),
        "missing_skills": keyword.get("skill_overlap", {}).get("missing_display", []),
        "missing_required": gaps.get("missing_required", []),
        "missing_preferred": gaps.get("missing_preferred", []),
        "priority_gaps": gaps.get("priority_gaps", []),
        "semantic_strengths": semantic.get("strengths", []),
        "semantic_gaps": semantic.get("gaps", []),
        "transferable_skills": semantic.get("transferable_skills", []),
        "rewritten_bullets": [
            {
                "original": r["original"],
                "rewritten": r["rewritten"],
                "faithful": r.get("validation", {}).get("is_faithful", True),
            }
            for r in rewrites
        ],
    }
