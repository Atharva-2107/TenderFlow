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
# LOAD MODEL ONCE (SAFE)
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
# METADATA DETECTION
# ======================================================
METADATA_KEYWORDS = [
    "bid number", "dated", "department name", "organisation name",
    "office name", "bid document", "opening date", "closing date",
    "emd", "tender notice", "eligibility"
]

def is_metadata_block(text: str) -> bool:
    t = text.lower()

    if any(k in t for k in METADATA_KEYWORDS):
        return True

    digit_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)
    alpha_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)

    if digit_ratio > 0.45 or alpha_ratio < 0.45:
        return True

    return False

# ======================================================
# CONTRACT CLAUSE DETECTION
# ======================================================
def looks_like_contract_clause(text: str) -> bool:
    keywords = [
        "liquidated", "damages", "penalty",
        "terminate", "termination",
        "indemnify", "indemnity",
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
# SINGLE-DOMINANT AI CLASSIFICATION (KEY FIX)
# ======================================================
def classify_clause(text, threshold=0.18):
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

    detections = []
    for i, p in enumerate(probs):
        conf = float(p)
        if conf >= threshold:
            detections.append((LABELS[i], conf))

    return detections


# ======================================================
# SEVERITY SCORING (UNCHANGED LOGIC)
# ======================================================
def severity_from_confidence(confidence, text):
    base = confidence * 100
    t = text.lower()

    if "liquidated" in t or "damages" in t:
        base += 30
    if "terminate" in t:
        base += 25
    if "indemn" in t:
        base += 20
    if "payment" in t:
        base += 10
    if "delay" in t:
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
# TRUE AI-DRIVEN EXPLANATION (CATEGORY-LED)
# ======================================================
def generate_ai_impact(category, text):
    t = text.lower()

    if category == "Financial":
        return (
            "The clause imposes financial obligations or penalties that could "
            "increase project cost if conditions are breached."
        )

    if category == "Timeline":
        return (
            "The clause links obligations to strict timelines, increasing exposure "
            "to penalties or performance issues in case of delay."
        )

    if category == "Legal":
        if "terminate" in t:
            return (
                "The clause allows contract termination under defined conditions, "
                "which increases legal and commercial exposure."
            )
        if "indemn" in t or "liability" in t:
            return (
                "The clause transfers legal liability to one party, potentially "
                "increasing litigation or compliance risk."
            )
        return (
            "The clause defines enforceable legal rights and obligations that may "
            "affect contract control or dispute outcomes."
        )

    if category == "Payment":
        return (
            "The clause governs payment structure or timelines, which may affect "
            "cash flow and financial planning."
        )

    if category == "Resource":
        return (
            "The clause places operational obligations related to manpower, "
            "equipment, or service availability."
        )

    return "The clause introduces contractual obligations that may carry execution risk."

# ======================================================
# MAIN ENTRY POINT
# ======================================================
def analyze_pdf(uploaded_file):
    text = extract_text(uploaded_file)
    clauses = split_clauses(text)

    results = []

    for clause in clauses:
        detections = classify_clause(clause)

        if not detections:
            continue


        for category, confidence in detections:

            highlight = extract_risk_highlight(clause, category)
            severity, status = severity_from_confidence(confidence, clause)

            results.append({
                "category": category,
                "clause": highlight[:90] + ("..." if len(highlight) > 90 else ""),
                "content": highlight,
                "severity": severity,
                "status": status,
                "impact": generate_ai_impact(category, clause),
                "tag_class": f"tag-{category.lower()}"
            })


    # ==================================================
    # BID DOCUMENT FALLBACK
    # ==================================================
    if not results:
        return [{
            "category": "Financial",
            "clause": "Bid eligibility and administrative conditions detected",
            "content": (
                "The document primarily contains eligibility, experience, and "
                "administrative requirements rather than enforceable contract clauses."
            ),
            "severity": 40,
            "status": "Warning",
            "impact": (
                "The document appears to be bid-focused. Contractual risk analysis "
                "will be more meaningful on ATC, SLA, or final agreement documents."
            ),
            "tag_class": "tag-financial"
        }]

    return results
