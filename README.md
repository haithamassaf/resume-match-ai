# ResumeMatch AI

An NLP-powered web app that analyzes how well your resume matches a job description. Upload a PDF resume, paste a job posting, and get an instant match score with actionable feedback.

**What it does:**
- Scores your resume-job fit using keyword matching + AI semantic analysis
- Identifies missing skills, sorted by priority (required vs. preferred)
- Breaks down match rates by category (ML, Cloud, Data Engineering, etc.)
- Rewrites your bullet points to better align with the job description
- Validates rewrites to prevent fabrication or scope inflation

## Quick Start

```bash
# Clone and set up
git clone https://github.com/haithamassaf/resume-match-ai.git
cd resume-match-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Add your API key (optional -- keyword matching works without it)
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the app
streamlit run frontend/app.py
```

## How It Works

```
Resume (PDF) + Job Description (text)
        |
        v
   [ Parsers ]  -- PDF text extraction (PyMuPDF), section detection,
        |           skill extraction via 70-category taxonomy
        v
   [ Analysis Engine ]
        |
        |-- Keyword Match: TF-IDF cosine similarity + alias-aware skill matching
        |-- Semantic Match: Claude API deep-fit analysis (strengths, gaps, transferable skills)
        |-- Gap Analysis: missing required/preferred skills, experience & education checks
        |-- Scorer: weighted composite (30% keyword, 40% semantic, 30% requirements)
        |
        v
   [ Bullet Rewriter ]  -- Claude API rewrites + truthfulness validation
        |
        v
   [ Streamlit Dashboard ]  -- score gauge, skill charts, side-by-side bullet comparison
```

## Features

### Match Scoring
Weighted composite score combining three signals:
- **Keyword match (30%)** -- TF-IDF text similarity + required/preferred skill overlap
- **Semantic match (40%)** -- Claude API analyzes experience alignment, transferable skills, and gaps
- **Requirements met (30%)** -- hard checks on skills, years of experience, and education

### Smart Skill Taxonomy
70 skill categories with 300+ aliases resolve variations automatically:
- "PostgreSQL" on your resume matches "SQL" in the job description
- "PyTorch" matches "deep learning frameworks"
- "GitHub Actions" matches "CI/CD"

### AI Bullet Rewriter
Rewrites resume bullets to incorporate job-specific keywords while preserving truthfulness. Every rewrite is validated against the original:
- Catches fabricated numbers and dollar amounts
- Flags scope inflation ("team" becoming "organization-wide")
- Blocks made-up achievements

### Export
Download rewritten bullets as plain text or the full analysis as a JSON report.

## Tech Stack

| Layer | Tech |
|-------|------|
| LLM | Claude API (claude-sonnet-4-20250514) |
| PDF Parsing | PyMuPDF (fitz) |
| NLP | spaCy + TF-IDF (scikit-learn) |
| Backend | FastAPI |
| Frontend | Streamlit + Plotly |

## Project Structure

```
resume-match-ai/
├── parsers/
│   ├── resume_parser.py        # PDF text extraction + section detection
│   ├── job_parser.py           # JD parsing + requirement classification
│   └── utils.py                # Text cleaning, skill extraction helpers
├── analysis/
│   ├── keyword_matcher.py      # TF-IDF + alias-aware exact matching
│   ├── semantic_matcher.py     # Claude API semantic analysis
│   ├── gap_analyzer.py         # Missing skills + requirements check
│   ├── scorer.py               # Weighted composite scoring
│   └── skill_taxonomy.py       # 70-category skill alias system
├── rewriter/
│   ├── bullet_rewriter.py      # Claude API bullet optimization
│   ├── prompts.py              # All prompt templates
│   └── validator.py            # Truthfulness validation
├── frontend/
│   ├── app.py                  # Streamlit app
│   └── components/
│       ├── upload.py           # PDF upload + JD text input
│       ├── score_gauge.py      # Plotly circular gauge
│       ├── skills_chart.py     # Category bar chart + skill pills
│       ├── bullet_compare.py   # Side-by-side bullet comparison
│       └── export.py           # Download buttons
├── data/
│   └── skill_aliases.json      # 70 skill categories, 300+ aliases
└── config/
    └── settings.py             # Environment config
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | (none) | Required for semantic analysis and bullet rewriting |
| `SPACY_MODEL` | `en_core_web_sm` | spaCy model for NLP |
| `KEYWORD_WEIGHT` | `0.30` | Weight for keyword match score |
| `SEMANTIC_WEIGHT` | `0.40` | Weight for semantic match score |
| `REQUIREMENTS_WEIGHT` | `0.30` | Weight for requirements-met score |

## Built With

Python, Claude API, PyMuPDF, spaCy, scikit-learn, Streamlit, Plotly
