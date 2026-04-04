"""Matched vs missing skills visualization."""

import plotly.graph_objects as go
import streamlit as st


def render_skills_overview(keyword_result: dict, gap_result: dict):
    """Render the skills analysis section with charts and details."""
    overlap = keyword_result["skill_overlap"]
    category_breakdown = keyword_result["category_breakdown"]

    # -- Top-level stats --
    cols = st.columns(4)
    cols[0].metric("Matched Skills", overlap["matched_count"])
    cols[1].metric("Missing Skills", overlap["missing_count"])
    cols[2].metric("Total JD Skills", overlap["total_jd_skills"])
    cols[3].metric("Overlap", f"{overlap['overlap_ratio']:.0%}")

    st.divider()

    # -- Category bar chart --
    _render_category_chart(category_breakdown)

    st.divider()

    # -- Matched vs Missing pills --
    col_match, col_miss = st.columns(2)

    with col_match:
        st.markdown("##### Matched Skills")
        if overlap["matched_display"]:
            _render_skill_pills(overlap["matched_display"], "green")
        else:
            st.caption("No matching skills found.")

    with col_miss:
        st.markdown("##### Missing Skills")
        if overlap["missing_display"]:
            _render_skill_pills(overlap["missing_display"], "red")
        else:
            st.caption("No missing skills -- great match!")

    # -- Extra skills (on resume but not in JD) --
    if overlap["extra_display"]:
        with st.expander(f"Extra Skills on Resume ({len(overlap['extra_display'])})"):
            _render_skill_pills(overlap["extra_display"], "blue")

    # -- Gap priority list --
    priority_gaps = gap_result.get("priority_gaps", [])
    if priority_gaps:
        st.divider()
        st.markdown("##### Priority Gaps")
        for gap in priority_gaps:
            icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(gap["priority"], "⚪")
            st.markdown(f"{icon} {gap['description']}")

    # -- Related skills hints --
    related = gap_result.get("related_skills", [])
    if related:
        with st.expander("Related Skills (you're close!)"):
            for r in related:
                st.markdown(
                    f"Missing **{r['missing']}** but you have "
                    f"**{', '.join(r['related_from_resume'])}** ({r['category']})"
                )


def _render_category_chart(category_breakdown: dict):
    """Render a horizontal bar chart of skill match rates by category."""
    # Filter to categories that have JD skills (score < 1.0 or have matched)
    cats = []
    scores = []
    colors = []
    for cat, data in sorted(category_breakdown.items()):
        if data["matched"] or data["missing"]:
            label = cat.replace("_", " ").title()
            cats.append(label)
            score = data["score"]
            scores.append(round(score * 100))
            if score >= 0.75:
                colors.append("#22c55e")
            elif score >= 0.5:
                colors.append("#eab308")
            else:
                colors.append("#ef4444")

    if not cats:
        return

    fig = go.Figure(go.Bar(
        x=scores,
        y=cats,
        orientation="h",
        marker_color=colors,
        text=[f"{s}%" for s in scores],
        textposition="auto",
    ))
    fig.update_layout(
        title="Skill Match by Category",
        xaxis=dict(range=[0, 105], title="Match %"),
        yaxis=dict(autorange="reversed"),
        height=max(200, len(cats) * 45 + 80),
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e0e0e0"},
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_skill_pills(skills: list, color: str):
    """Render skills as colored inline badges."""
    color_map = {
        "green": ("rgba(34,197,94,0.15)", "#22c55e"),
        "red": ("rgba(239,68,68,0.15)", "#ef4444"),
        "blue": ("rgba(59,130,246,0.15)", "#3b82f6"),
    }
    bg, border = color_map.get(color, ("rgba(128,128,128,0.15)", "#888"))

    pills_html = " ".join(
        f'<span style="display:inline-block;padding:4px 12px;margin:3px;'
        f"border-radius:16px;background:{bg};border:1px solid {border};"
        f'font-size:0.85em;">{skill}</span>'
        for skill in skills
    )
    st.markdown(pills_html, unsafe_allow_html=True)
