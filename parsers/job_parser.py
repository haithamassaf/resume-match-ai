import re

from parsers.utils import (
    clean_text,
    extract_education,
    extract_years_of_experience,
    load_skill_aliases,
    normalize_text,
    split_into_sentences,
)

# Patterns that indicate required vs preferred qualifications
REQUIRED_INDICATORS = [
    "required", "must have", "must be", "requirements", "minimum qualifications",
    "basic qualifications", "what you need", "what we require", "you have", "you bring",
]
PREFERRED_INDICATORS = [
    "preferred", "nice to have", "bonus", "plus", "ideal", "desired",
    "preferred qualifications", "additional qualifications", "it's a plus",
    "nice-to-have", "a plus",
]

# Section header patterns for job descriptions
JD_SECTION_PATTERNS = {
    "responsibilities": r"(?:key\s+)?responsibilities|what you'?ll do|the role|about the role|job duties|duties",
    "required": r"(?:required|minimum|basic)\s+qualifications?|requirements?|what you need|what we require|must.have|you have|you bring",
    "preferred": r"(?:preferred|desired|additional|bonus)\s+qualifications?|nice.to.have|plus|ideal candidate",
    "about": r"about (?:the )?(?:role|position|job|team|us|company)|overview|description|who we are",
    "benefits": r"benefits?|perks?|what we offer|compensation",
}


def parse_job_description(text: str) -> dict:
    """Parse a job description into structured components.

    Returns a dict with:
    - raw_text: cleaned full text
    - sections: detected sections and their content
    - required_skills: skills identified as required
    - preferred_skills: skills identified as preferred
    - all_skills: all skills mentioned anywhere
    - responsibilities: list of key responsibilities
    - years_of_experience: experience requirements
    - education: education requirements
    - requirement_classification: skills split by required/preferred
    """
    text = clean_text(text)
    sections = _detect_jd_sections(text)

    all_skills = _extract_skills(text)
    required_skills, preferred_skills = _classify_requirements(text, sections, all_skills)
    responsibilities = _extract_responsibilities(text, sections)
    years_of_exp = extract_years_of_experience(text)
    education = extract_education(text)

    return {
        "raw_text": text,
        "sections": sections,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "all_skills": all_skills,
        "responsibilities": responsibilities,
        "years_of_experience": years_of_exp,
        "education": education,
        "requirement_classification": {
            "required": required_skills,
            "preferred": preferred_skills,
        },
    }


def _detect_jd_sections(text: str) -> dict[str, str]:
    """Detect sections in a job description."""
    lines = text.split("\n")
    section_order: list[tuple[int, str]] = []

    for i, line in enumerate(lines):
        stripped = line.strip().rstrip(":")
        if not stripped or len(stripped) > 80:
            continue

        for section_key, pattern in JD_SECTION_PATTERNS.items():
            if re.search(pattern, stripped, re.IGNORECASE):
                section_order.append((i, section_key))
                break

    section_order.sort(key=lambda x: x[0])

    result: dict[str, str] = {}
    for idx, (start_line, key) in enumerate(section_order):
        if idx + 1 < len(section_order):
            end_line = section_order[idx + 1][0]
        else:
            end_line = len(lines)

        section_text = "\n".join(lines[start_line + 1 : end_line])
        result[key] = clean_text(section_text)

    if not result:
        result["raw"] = text

    return result


def _extract_skills(text: str) -> list[str]:
    """Extract all skills mentioned in the text using the taxonomy."""
    aliases = load_skill_aliases()
    normalized = normalize_text(text)
    found = []

    for canonical, variants in aliases.items():
        for variant in variants:
            if len(variant) <= 3:
                pattern = rf"\b{re.escape(variant)}\b"
            else:
                pattern = rf"(?<!\w){re.escape(variant)}(?!\w)"

            if re.search(pattern, normalized):
                found.append(canonical)
                break

    return sorted(set(found))


def _classify_requirements(
    text: str, sections: dict[str, str], all_skills: list[str]
) -> tuple[list[str], list[str]]:
    """Classify skills as required or preferred based on context."""
    required = set()
    preferred = set()

    # If we have explicit required/preferred sections, use those
    if "required" in sections:
        required_skills = _extract_skills(sections["required"])
        required.update(required_skills)
    if "preferred" in sections:
        preferred_skills = _extract_skills(sections["preferred"])
        preferred.update(preferred_skills)

    # For skills not yet classified, check surrounding context
    if required or preferred:
        unclassified = set(all_skills) - required - preferred
        # Default unclassified skills to required (conservative approach)
        required.update(unclassified)
    else:
        # No explicit sections found -- use sentence-level context
        normalized = normalize_text(text)
        sentences = split_into_sentences(normalized)
        aliases = load_skill_aliases()

        for skill in all_skills:
            classified = False
            variants = aliases.get(skill, [skill])

            for sentence in sentences:
                has_skill = any(v in sentence for v in variants)
                if not has_skill:
                    continue

                if any(ind in sentence for ind in PREFERRED_INDICATORS):
                    preferred.add(skill)
                    classified = True
                    break
                elif any(ind in sentence for ind in REQUIRED_INDICATORS):
                    required.add(skill)
                    classified = True
                    break

            if not classified:
                required.add(skill)  # Default to required

    return sorted(required), sorted(preferred)


def _extract_responsibilities(text: str, sections: dict[str, str]) -> list[str]:
    """Extract key responsibilities from the job description."""
    # Prefer the responsibilities section if it exists
    source = sections.get("responsibilities", text)

    responsibilities = []
    # Match bullet points and numbered items
    patterns = [
        r"^[\s]*[•\-\u2022\u2023\u25E6\u2043\u2219\*►▪‣]\s*(.+)",
        r"^[\s]*\d+[.)]\s*(.+)",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, source, re.MULTILINE):
            resp = match.group(1).strip()
            if len(resp) > 15:  # Skip very short fragments
                responsibilities.append(resp)

    # If no bullets found, fall back to sentences from the section
    if not responsibilities and "responsibilities" in sections:
        responsibilities = split_into_sentences(sections["responsibilities"])

    return responsibilities
