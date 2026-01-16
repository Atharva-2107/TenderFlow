# utils/complexity.py
from PyPDF2 import PdfReader

# ----------------------------
# Keyword dictionaries
# ----------------------------
TECHNICAL_KEYWORDS = {
    "tunnel": 3,
    "bridge": 3,
    "metro": 2,
    "viaduct": 3,
    "pile foundation": 2,
    "deep foundation": 2,
    "prestressed": 2,
    "post tension": 2,
}

RISK_KEYWORDS = {
    "hazardous": 3,
    "risk": 2,
    "confined space": 3,
    "working at height": 2,
    "live traffic": 2,
    "safety compliance": 1,
}

LEGAL_KEYWORDS = {
    "liquidated damages": 2,
    "penalty": 2,
    "arbitration": 1,
    "termination": 2,
    "force majeure": 1,
}

SCHEDULE_KEYWORDS = {
    "time is essence": 3,
    "strict timeline": 2,
    "fast track": 2,
    "emergency": 3,
}

# ----------------------------
# Extract raw text
# ----------------------------
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    return " ".join([p.extract_text() or "" for p in reader.pages]).lower()

# ----------------------------
# Compute complexity score
# ----------------------------
def compute_complexity_score(pdf_file):
    text = extract_text_from_pdf(pdf_file)
    score = 0

    def apply_keywords(keyword_dict):
        nonlocal score
        for word, weight in keyword_dict.items():
            if word in text:
                score += weight

    apply_keywords(TECHNICAL_KEYWORDS)
    apply_keywords(RISK_KEYWORDS)
    apply_keywords(LEGAL_KEYWORDS)
    apply_keywords(SCHEDULE_KEYWORDS)

    # Normalize to 1–10
    return min(10, max(1, round(score / 2)))
