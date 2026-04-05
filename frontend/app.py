"""ResumeMatch AI -- Streamlit frontend."""

import sys
from pathlib import Path

# Add project root to path so imports work when running via `streamlit run`
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from config.settings import ANTHROPIC_API_KEY
from frontend.components.bullet_compare import render_bullet_comparison
from frontend.components.export import render_export_section
from frontend.components.score_gauge import render_score_gauge
from frontend.components.skills_chart import render_skills_overview
from frontend.components.upload import render_upload_section
from parsers.job_parser import parse_job_description
from parsers.resume_parser import parse_resume


# ── Analysis pipeline ────────────────────────────────────────
def _run_analysis(pdf_path: str, jd_text: str, use_semantic: bool, use_rewriter: bool):
    # -- Step 1: Parse inputs --
    with st.status("Parsing resume and job description...", expanded=True) as status:
        st.write("Extracting text from PDF...")
        resume_data = parse_resume(pdf_path)
        resume_text = resume_data["raw_text"]
        resume_skills = resume_data["skills"]
        bullet_points = resume_data["bullet_points"]

        st.write("Parsing job description...")
        jd_data = parse_job_description(jd_text)

        st.write(
            f"Found **{len(resume_skills)}** skills in resume, "
            f"**{len(jd_data['all_skills'])}** in job description, "
            f"**{len(bullet_points)}** bullet points."
        )
        status.update(label="Parsing complete!", state="complete")

    # -- Step 2: Run analysis --
    with st.status("Running match analysis...", expanded=True) as status:
        from analysis.scorer import run_full_analysis

        if use_semantic:
            st.write("Running keyword matching + AI semantic analysis...")
        else:
            st.write("Running keyword matching...")

        result = run_full_analysis(
            resume_text=resume_text,
            jd_text=jd_text,
            resume_skills=resume_skills,
            jd_data=jd_data,
            use_semantic=use_semantic,
        )
        status.update(label="Analysis complete!", state="complete")

    # -- Step 3: Rewrite bullets --
    rewrites = []
    if use_rewriter and bullet_points:
        with st.status("Rewriting bullet points...", expanded=True) as status:
            from rewriter.bullet_rewriter import build_jd_context, rewrite_bullets_batch
            from rewriter.validator import validate_batch

            st.write(f"Rewriting {len(bullet_points)} bullets to match the JD...")
            jd_context = build_jd_context(jd_data)
            rewrites = rewrite_bullets_batch(bullet_points, jd_context)

            st.write("Validating rewrites for truthfulness...")
            rewrites = validate_batch(rewrites, use_api=False)

            faithful = sum(1 for r in rewrites if r.get("validation", {}).get("is_faithful", True))
            st.write(f"**{faithful}/{len(rewrites)}** rewrites passed validation.")
            status.update(label="Rewriting complete!", state="complete")

    # -- Display results --
    st.divider()

    # Score gauge
    st.header("Match Score")
    render_score_gauge(result["overall"])

    # Semantic insights (if available)
    semantic = result.get("semantic", {})
    if semantic.get("strengths") or semantic.get("gaps"):
        st.divider()
        st.header("AI Insights")
        col_s, col_g = st.columns(2)
        with col_s:
            st.markdown("##### Strengths")
            for s in semantic.get("strengths", []):
                st.markdown(f"- {s}")
        with col_g:
            st.markdown("##### Gaps")
            for g in semantic.get("gaps", []):
                st.markdown(f"- {g}")

        transferable = semantic.get("transferable_skills", [])
        if transferable:
            st.markdown("##### Transferable Skills")
            st.markdown(", ".join(transferable))

    # Skills breakdown
    st.divider()
    st.header("Skills Analysis")
    render_skills_overview(result["keyword"], result["gaps"])

    # Bullet comparison
    if rewrites:
        st.divider()
        st.header("Bullet Point Rewrites")
        st.caption("Original (left) vs. AI-optimized (right)")
        render_bullet_comparison(rewrites)

    # Export
    st.divider()
    st.header("Export")
    render_export_section(result, rewrites, resume_skills)


# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="ResumeMatch AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Header ───────────────────────────────────────────────────
st.title("ResumeMatch AI")
st.caption("Upload your resume and paste a job description to see how well you match.")

st.divider()

# ── Sidebar settings ─────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    use_semantic = st.toggle(
        "Enable AI Semantic Analysis",
        value=bool(ANTHROPIC_API_KEY),
        help="Uses Claude API for deeper analysis. Requires ANTHROPIC_API_KEY.",
    )
    use_rewriter = st.toggle(
        "Enable AI Bullet Rewriter",
        value=bool(ANTHROPIC_API_KEY),
        help="Rewrites resume bullets to match the JD. Requires ANTHROPIC_API_KEY.",
    )
    if (use_semantic or use_rewriter) and not ANTHROPIC_API_KEY:
        st.warning("Set ANTHROPIC_API_KEY in your .env file to use AI features.")
        use_semantic = False
        use_rewriter = False

# ── Upload section ───────────────────────────────────────────
pdf_path, jd_text = render_upload_section()

# ── Analyze button ───────────────────────────────────────────
can_analyze = pdf_path is not None and len(jd_text.strip()) > 50

if can_analyze:
    analyze_clicked = st.button("Analyze Match", type="primary", use_container_width=True)
else:
    st.button(
        "Analyze Match",
        type="primary",
        use_container_width=True,
        disabled=True,
        help="Upload a resume PDF and paste a job description (50+ characters) to start.",
    )
    analyze_clicked = False

if analyze_clicked:
    _run_analysis(pdf_path, jd_text, use_semantic, use_rewriter)

# ── Footer ───────────────────────────────────────────────────
st.divider()
st.caption("Built by Haitham Assaf")
