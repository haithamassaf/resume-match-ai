import re
from pathlib import Path

import fitz  # PyMuPDF

from parsers.utils import (
    clean_text,
    extract_bullet_points,
    extract_years_of_experience,
    load_skill_aliases,
    normalize_text,
)

# Section headers commonly found in resumes
SECTION_PATTERNS = {
    "experience": r"(?:work\s+)?experience|employment\s+history|professional\s+experience|work\s+history",
    "education": r"education|academic|degrees?|certifications?\s*(?:&|and)?\s*education",
    "skills": r"skills|technical\s+skills|core\s+competencies|technologies|proficiencies|tools?\s*(?:&|and)?\s*technologies",
    "projects": r"projects|personal\s+projects|portfolio|key\s+projects",
    "certifications": r"certifications?|licenses?|credentials?",
    "summary": r"summary|objective|profile|about\s+me|professional\s+summary",
    "publications": r"publications?|papers?|research",
    "awards": r"awards?|honors?|achievements?",
}


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from a PDF file using PyMuPDF."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF file: {pdf_path}")

    doc = fitz.open(pdf_path)
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()

    return clean_text("\n".join(text_parts))


def detect_sections(text: str) -> dict[str, str]:
    """Identify and extract resume sections by header patterns.

    Returns a dict mapping section names to their text content.
    """
    lines = text.split("\n")
    sections: dict[str, tuple[int, str]] = {}  # section -> (line_index, pattern_key)
    section_order: list[tuple[int, str]] = []  # (line_index, section_key)

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or len(stripped) > 60:
            continue

        for section_key, pattern in SECTION_PATTERNS.items():
            if re.match(rf"^{pattern}$", stripped, re.IGNORECASE):
                sections[section_key] = (i, section_key)
                section_order.append((i, section_key))
                break

    # Sort sections by their position in the document
    section_order.sort(key=lambda x: x[0])

    # Extract text between section headers
    result: dict[str, str] = {}
    for idx, (start_line, key) in enumerate(section_order):
        if idx + 1 < len(section_order):
            end_line = section_order[idx + 1][0]
        else:
            end_line = len(lines)

        # Skip the header line itself
        section_text = "\n".join(lines[start_line + 1 : end_line])
        result[key] = clean_text(section_text)

    # If no sections detected, put everything under "raw"
    if not result:
        result["raw"] = text

    return result


def extract_skills_from_text(text: str) -> list[str]:
    """Extract skills by matching against the skill taxonomy."""
    aliases = load_skill_aliases()
    normalized = normalize_text(text)
    found_skills = []

    for canonical, variants in aliases.items():
        for variant in variants:
            # Use word boundary matching for short terms, substring for longer ones
            if len(variant) <= 3:
                pattern = rf"\b{re.escape(variant)}\b"
            else:
                pattern = rf"(?<!\w){re.escape(variant)}(?!\w)"

            if re.search(pattern, normalized):
                found_skills.append(canonical)
                break  # Found one variant, move to next canonical skill

    return sorted(set(found_skills))


def parse_resume(pdf_path: str) -> dict:
    """Full resume parsing pipeline.

    Returns a structured dict with:
    - raw_text: full extracted text
    - sections: dict of detected sections and their content
    - skills: list of identified skills (canonical names)
    - bullet_points: list of extracted bullet points
    - years_of_experience: extracted experience mentions
    """
    raw_text = extract_text_from_pdf(pdf_path)
    sections = detect_sections(raw_text)

    # Extract skills from the full text (skills appear everywhere, not just skills section)
    skills = extract_skills_from_text(raw_text)

    # Extract bullet points from experience and projects sections
    bullet_text_parts = []
    for key in ["experience", "projects"]:
        if key in sections:
            bullet_text_parts.append(sections[key])
    # Fall back to full text if no sections detected
    if not bullet_text_parts:
        bullet_text_parts.append(raw_text)

    bullet_points = extract_bullet_points("\n".join(bullet_text_parts))

    # Extract years of experience
    years_of_exp = extract_years_of_experience(raw_text)

    return {
        "raw_text": raw_text,
        "sections": sections,
        "skills": skills,
        "bullet_points": bullet_points,
        "years_of_experience": years_of_exp,
    }
