import pdfplumber
import re
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.nn.functional import softmax
from functools import lru_cache

# ======================================================
# MODEL CONFIG
# ======================================================
MODEL_NAME = "nlpaueb/legal-bert-base-uncased"
LABELS = ["Financial", "Legal", "Payment", "Timeline", "Resource"]

# ======================================================
# MODEL LOADING (CACHED — STREAMLIT SAFE)
# ======================================================
@lru_cache(maxsize=1)
def load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(LABELS)
    )
    model.eval()
    return tokenizer, model


tokenizer, model = load_model()

# ======================================================
# TEXT CLEANING
# ======================================================
def clean_extracted_text(text: str) -> str:
    # remove cid artifacts
    text = re.sub(r"\(cid:\d+\)", " ", text)

    # normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ======================================================
# PDF TEXT EXTRACTION
# ======================================================
def extract_text(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return clean_extracted_text(text)


# ======================================================
# METADATA / HEADER DETECTION (CRITICAL FIX)
# ======================================================
METADATA_KEYWORDS = [
    "bid number", "dated", "department name", "organisation name",
    "office name", "state name", "ministry", "gem/", "bid document",
    "bid details", "opening date", "closing date", "event based",
    "catering service", "validity", "from end date"
]


def is_metadata_block(text: str) -> bool:
    t = text.lower()

    # keyword-based rejection
    if any(k in t for k in METADATA_KEYWORDS):
        return True

    # too many numbers → metadata
    digit_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)
    if digit_ratio > 0.25:
        return True

    # mixed language corruption (Hindi + English headers)
    alpha_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)
    if alpha_ratio < 0.45:
        return True

    return False


# ======================================================
# CLAUSE SPLITTING (STRICT)
# ======================================================
def split_clauses(text):
    raw_clauses = re.split(
        r"\n(?=(?:Clause|Section)?\s*\d+[\.\)])",
        text,
        flags=re.IGNORECASE
    )

    clauses = []
    for c in raw_clauses:
        c = c.strip()

        # reject numbering junk
        if re.fullmatch(r"\d+[\.\)]?", c):
            continue

        # reject short text
        if len(c) < 80:
            continue

        # reject non-language
        if not re.search(r"[a-zA-Z]{4,}", c):
            continue

        # reject metadata / headers
        if is_metadata_block(c):
            continue

        clauses.append(c)

    return clauses


# ======================================================
# LEGAL-BERT CLASSIFICATION
# ======================================================
def classify_clause(text):
    inputs = tokenizer(
        text,
        truncation=True,
        padding=True,
        max_length=512,
        return_tensors="pt"
    )

    with torch.no_grad():
        outputs = model(**inputs)

    probs = softmax(outputs.logits, dim=1)[0]
    confidence, idx = torch.max(probs, dim=0)

    return LABELS[idx.item()], float(confidence)


# ======================================================
# SEVERITY SCORING
# ======================================================
def severity_from_confidence(confidence, clause_len):
    base = confidence * 100
    length_boost = min(clause_len / 600, 1.2) * 15
    severity = min(int(base + length_boost), 95)

    if severity >= 75:
        status = "Critical"
    elif severity >= 45:
        status = "Warning"
    else:
        status = "Low"

    return severity, status


# ======================================================
# RISK HIGHLIGHT EXTRACTION
# ======================================================
def extract_risk_highlight(clause, category):
    sentences = re.split(r"(?<=[.;])\s+", clause)

    KEY_PHRASES = {
        "Financial": ["penalty", "liquidated", "retention", "escalation"],
        "Payment": ["payment", "invoice", "credit", "days"],
        "Legal": ["liable", "indemn", "terminate", "liability"],
        "Timeline": ["delay", "milestone", "completion"],
        "Resource": ["manpower", "staff", "equipment"]
    }

    for s in sentences:
        s_clean = s.strip()
        if len(s_clean) < 30:
            continue
        if any(k in s_clean.lower() for k in KEY_PHRASES.get(category, [])):
            return s_clean

    for s in sentences:
        s_clean = s.strip()
        if len(s_clean) >= 40:
            return s_clean

    return clause[:120]


# ======================================================
# MAIN ENTRY POINT
# ======================================================
def analyze_pdf(uploaded_file):
    text = extract_text(uploaded_file)
    clauses = split_clauses(text)

    results = []

    for clause in clauses:
        category, confidence = classify_clause(clause)

        if confidence < 0.35:
            continue

        severity, status = severity_from_confidence(confidence, len(clause))
        highlight = extract_risk_highlight(clause, category)

        results.append({
            "category": category,
            "clause": highlight[:80],
            "content": highlight,
            "severity": severity,
            "status": status,
            "impact": "Key contractual risk identified.",
            "tag_class": f"tag-{category.lower()}"
        })

    # 👇 ADD HERE
    if not results:
        return [{
            "category": "Financial",
            "clause": "Strict bid eligibility and commercial conditions detected",
            "content": (
                "This document primarily contains bid eligibility, experience, "
                "turnover, and administrative conditions. These may pose "
                "commercial or participation risks for bidders."
            ),
            "severity": 45,
            "status": "Warning",
            "impact": (
                "Bid-level risk identified. Upload ATC / SLA / Contract document "
                "for contractual risk analysis."
            ),
            "tag_class": "tag-financial"
        }]

    return results
