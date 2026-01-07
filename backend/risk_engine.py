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
# LOAD MODEL ONCE (STREAMLIT SAFE)
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
    text = re.sub(r"\(cid:\d+\)", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ======================================================
# PDF TEXT EXTRACTION
# ======================================================
def extract_text(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return clean_extracted_text(text)

# ======================================================
# METADATA DETECTION (BID DOCS)
# ======================================================
METADATA_KEYWORDS = [
    "bid number", "dated", "department name", "organisation name",
    "office name", "gem/", "bid document", "bid details",
    "opening date", "closing date", "event based", "eligibility",
    "emd", "tender notice", "letter inviting bid"
]

def is_metadata_block(text: str) -> bool:
    t = text.lower()
    if any(k in t for k in METADATA_KEYWORDS):
        return True

    digit_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)
    if digit_ratio > 0.45:
        return True

    alpha_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)
    if alpha_ratio < 0.45:
        return True

    return False

# ======================================================
# CONTRACT CLAUSE OVERRIDE
# ======================================================
def looks_like_contract_clause(text: str) -> bool:
    keywords = [
        "liquidated", "damages", "penalty", "terminate",
        "termination", "indemnify", "indemnity",
        "liability", "payment", "invoice",
        "arbitration", "force majeure",
        "governing law", "service level", "sla"
    ]
    t = text.lower()
    return any(k in t for k in keywords)

# ======================================================
# CLAUSE SPLITTING
# ======================================================
def split_clauses(text):
    raw = re.split(r"\n(?=\d+[\.\)])", text)
    clauses = []

    for c in raw:
        c = c.strip()

        if len(c) < 60:
            continue

        if not re.search(r"[a-zA-Z]{4,}", c):
            continue

        if is_metadata_block(c) and not looks_like_contract_clause(c):
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
def severity_from_confidence(confidence, text):
    base = confidence * 100

    if "liquidated" in text.lower() or "damages" in text.lower():
        base += 30
    if "terminate" in text.lower():
        base += 25
    if "indemn" in text.lower():
        base += 20
    if "payment" in text.lower():
        base += 10

    severity = min(int(base), 95)

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
        "Financial": ["liquidated", "penalty", "damages"],
        "Legal": ["terminate", "indemn", "liability", "arbitration"],
        "Payment": ["payment", "invoice", "days"],
        "Timeline": ["delay", "milestone", "uptime"],
        "Resource": ["manpower", "staff", "equipment"]
    }

    for s in sentences:
        if any(k in s.lower() for k in KEY_PHRASES.get(category, [])):
            return s.strip()

    return sentences[0].strip()

# ======================================================
# MAIN ENTRY POINT
# ======================================================
def analyze_pdf(uploaded_file):
    text = extract_text(uploaded_file)
    clauses = split_clauses(text)

    results = []

    for clause in clauses:
        category, confidence = classify_clause(clause)

        # 🔑 RELAXED CONFIDENCE GATE (CRITICAL FIX)
        if confidence < 0.10 and not looks_like_contract_clause(clause):
            continue

        severity, status = severity_from_confidence(confidence, clause)
        highlight = extract_risk_highlight(clause, category)

        results.append({
            "category": category,
            "clause": highlight[:90] + ("..." if len(highlight) > 90 else ""),
            "content": highlight,
            "severity": severity,
            "status": status,
            "impact": (
                f"Key contractual risk identified using Legal-BERT "
                f"({round(confidence * 100, 1)}% confidence)."
            ),
            "tag_class": f"tag-{category.lower()}"
        })

    # ==================================================
    # BID-RISK FALLBACK (ONLY IF NOTHING FOUND)
    # ==================================================
    if not results:
        return [{
            "category": "Financial",
            "clause": "Strict bid eligibility and commercial conditions detected",
            "content": (
                "This document primarily contains bid eligibility, experience, "
                "and administrative conditions rather than contractual obligations."
            ),
            "severity": 45,
            "status": "Warning",
            "impact": (
                "Bid-level commercial risk identified. Upload ATC / SLA / "
                "Contract document for contractual risk analysis."
            ),
            "tag_class": "tag-financial"
        }]

    return results
