import os
from dotenv import load_dotenv

load_dotenv()


def _get_secret(key: str, default: str = "") -> str:
    """Get a secret from environment or Streamlit Cloud secrets."""
    val = os.getenv(key, "")
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


# API Keys
ANTHROPIC_API_KEY = _get_secret("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# spaCy
SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_sm")

# Scoring Weights
KEYWORD_WEIGHT = float(os.getenv("KEYWORD_WEIGHT", "0.30"))
SEMANTIC_WEIGHT = float(os.getenv("SEMANTIC_WEIGHT", "0.40"))
REQUIREMENTS_WEIGHT = float(os.getenv("REQUIREMENTS_WEIGHT", "0.30"))
