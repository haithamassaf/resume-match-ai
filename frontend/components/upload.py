"""PDF upload and job description text input components."""

import tempfile
from pathlib import Path

import streamlit as st


def render_upload_section() -> tuple:
    """Render the resume upload and JD input section.

    Returns:
        (pdf_path, jd_text) -- pdf_path is a temp file path or None,
        jd_text is the raw job description string or empty string.
    """
    col1, col2 = st.columns(2)

    pdf_path = None
    with col1:
        st.subheader("Resume")
        uploaded_file = st.file_uploader(
            "Upload your resume PDF",
            type=["pdf"],
            help="Supports single-page and multi-page PDF resumes.",
        )
        if uploaded_file is not None:
            # Write to temp file so PyMuPDF can read it
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            tmp.write(uploaded_file.read())
            tmp.flush()
            pdf_path = tmp.name
            st.success(f"Uploaded: {uploaded_file.name}")

    jd_text = ""
    with col2:
        st.subheader("Job Description")
        jd_text = st.text_area(
            "Paste the job description here",
            height=300,
            placeholder=(
                "Paste the full job posting including responsibilities, "
                "requirements, and preferred qualifications..."
            ),
        )

    return pdf_path, jd_text
