import re
import json
from pathlib import Path


def load_skill_aliases() -> dict[str, list[str]]:
    """Load the skill taxonomy from skill_aliases.json."""
    path = Path(__file__).parent.parent / "data" / "skill_aliases.json"
    with open(path) as f:
        return json.load(f)


def clean_text(text: str) -> str:
    """Clean extracted text by normalizing whitespace and removing artifacts."""
    # Replace multiple newlines with double newline
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Replace multiple spaces with single space
    text = re.sub(r" {2,}", " ", text)
    # Remove non-printable characters (keep newlines and tabs)
    text = re.sub(r"[^\S\n\t]+", " ", text)
    # Strip leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    # Remove leading/trailing whitespace
    return text.strip()


def normalize_text(text: str) -> str:
    """Lowercase and normalize text for matching purposes."""
    text = text.lower()
    # Normalize common separators
    text = text.replace("–", "-").replace("—", "-")
    # Normalize slashes with spaces around them
    text = re.sub(r"\s*/\s*", "/", text)
    return text


def extract_bullet_points(text: str) -> list[str]:
    """Extract individual bullet points from resume text."""
    bullets = []
    # Match lines starting with bullet markers
    pattern = r"^[\s]*[•\-\u2022\u2023\u25E6\u2043\u2219\*►▪‣]\s*(.+)"
    for match in re.finditer(pattern, text, re.MULTILINE):
        bullet = match.group(1).strip()
        if len(bullet) > 10:  # Skip very short fragments
            bullets.append(bullet)
    return bullets


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    # Split on period, exclamation, question mark followed by space or end
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 5]


def extract_years_of_experience(text: str) -> list[dict]:
    """Extract years of experience requirements from text."""
    patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)[\s\w]*(?:of\s+)?(?:experience|exp)",
        r"(?:experience|exp)[\s\w]*(\d+)\+?\s*(?:years?|yrs?)",
        r"(\d+)\+?\s*(?:years?|yrs?)[\s\w]*(?:in|with|of)",
    ]
    results = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            years = int(match.group(1))
            context = text[max(0, match.start() - 30):match.end() + 30].strip()
            results.append({"years": years, "context": context})
    return results


def extract_education(text: str) -> list[str]:
    """Extract education-related requirements from text."""
    degree_patterns = [
        r"(?:bachelor'?s?|b\.?s\.?|b\.?a\.?)\s+(?:degree\s+)?(?:in\s+)?[A-Za-z\s,/&]{3,50}",
        r"(?:master'?s?|m\.?s\.?|m\.?a\.?|mba)\s+(?:degree\s+)?in\s+[A-Za-z\s,/&]{3,50}",
        r"(?:ph\.?d\.?|doctorate)\s+(?:degree\s+)?(?:in\s+)?[A-Za-z\s,/&]{3,50}",
        r"(?:degree|diploma)\s+in\s+[A-Za-z\s,/&]{3,50}",
    ]
    results = []
    for pattern in degree_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Trim trailing whitespace/newlines from greedy match
            edu = re.sub(r"[\n\r].*", "", match.group(0)).strip().rstrip(",. ")
            if len(edu) > 10:
                # Skip if this is a substring of an already-found result
                if not any(edu.lower() in existing.lower() for existing in results):
                    # Remove any existing results that are substrings of this one
                    results = [r for r in results if r.lower() not in edu.lower()]
                    results.append(edu)
    return results
