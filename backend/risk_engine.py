import pdfplumber
import re
import torch
import streamlit as st
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.nn.functional import softmax

# ======================================================
# MODEL CONFIG
# ======================================================
MODEL_NAME = "nlpaueb/legal-bert-base-uncased"
LABELS = ["Financial", "Legal", "Payment", "Timeline", "Resource"]

torch.set_num_threads(4)
torch.backends.mkldnn.enabled = True


# ======================================================
# STREAMLIT RESOURCE CACHE
# ======================================================
@st.cache_resource(show_spinner="Loading AI Risk Engine...")
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
# TEXT EXTRACTION
# ======================================================
def clean_extracted_text(text: str) -> str:
    text = re.sub(r"\(cid:\d+\)", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_text(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return clean_extracted_text(text)


# ======================================================
# CLAUSE SPLITTING
# ======================================================
def split_clauses(text):
    raw = re.split(r"\n(?=\d+[\.\)])", text)
    clauses = []

    for c in raw:
        c = c.strip()
        if len(c) < 80:
            continue
        if not re.search(r"[a-zA-Z]{4,}", c):
            continue
        clauses.append(c)

    return clauses


# ======================================================
# AI GATE (PERFORMANCE)
# ======================================================
HARD_KEYWORDS = [
    "payment", "compensation", "fees", "charges",
    "delay", "time", "completion", "schedule",
    "penalty", "liquidated", "damages",
    "terminate", "termination", "indemn",
    "liability", "arbitration", "court",
    "fsi", "tdr", "premium"
]


def requires_ai_analysis(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in HARD_KEYWORDS) or len(t.split()) > 40


# ======================================================
# PRIMARY AI CLASSIFICATION (1 label per clause)
# ======================================================
def classify_clauses_batch(texts, threshold=0.12, batch_size=8):
    results = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        inputs = tokenizer(
            batch,
            truncation=True,
            padding=True,
            max_length=256,
            return_tensors="pt"
        )

        with torch.inference_mode():
            outputs = model(**inputs)

        probs = softmax(outputs.logits, dim=1)

        for text, row in zip(batch, probs):
            best_idx = int(torch.argmax(row))
            confidence = float(row[best_idx])

            if confidence >= threshold:
                results.append((text, LABELS[best_idx], confidence))
            else:
                results.append((text, None, 0.0))

    return results


# ======================================================
# RISK EXPANSION (DOMAIN-AWARE)
# ======================================================
def expand_related_risks(primary_category, text):
    t = text.lower()
    risks = set()

    if primary_category:
        risks.add(primary_category)

    PAYMENT_TERMS = [
        "payment", "payments", "paid", "payable",
        "compensation", "hardship", "displacement",
        "corpus fund", "fees", "charges",
        "gst", "stamp duty", "premium"
    ]

    TIMELINE_TERMS = [
        "time schedule", "completion period",
        "completion time", "within", "months",
        "days", "delay", "milestone", "handover"
    ]

    FINANCIAL_TERMS = [
        "liquidated", "penalty", "damages",
        "cost", "expense", "fsi", "tdr", "fungible"
    ]

    LEGAL_TERMS = [
        "terminate", "termination",
        "indemn", "liability",
        "arbitration", "court", "litigation"
    ]

    RESOURCE_TERMS = [
        "manpower", "staff", "labour",
        "equipment", "machinery"
    ]

    if any(k in t for k in PAYMENT_TERMS):
        risks.add("Payment")

    if any(k in t for k in TIMELINE_TERMS):
        risks.add("Timeline")

    if any(k in t for k in FINANCIAL_TERMS):
        risks.add("Financial")

    if any(k in t for k in LEGAL_TERMS):
        risks.add("Legal")

    if any(k in t for k in RESOURCE_TERMS):
        risks.add("Resource")

    return list(risks)


# ======================================================
# SEVERITY
# ======================================================
def severity_from_confidence(confidence, text):
    base = confidence * 100
    t = text.lower()

    if "liquidated" in t or "penalty" in t:
        base += 30
    if "delay" in t:
        base += 20
    if "terminate" in t:
        base += 25
    if "compensation" in t or "payment" in t:
        base += 15

    severity = min(int(base), 95)

    if severity >= 75:
        return severity, "Critical"
    elif severity >= 45:
        return severity, "Warning"
    return severity, "Low"


# ======================================================
# HIGHLIGHT
# ======================================================
def extract_risk_highlight(text, category):
    return text.strip()


# ======================================================
# AI IMPACT
# ======================================================
def generate_ai_impact(category, text):
    if category == "Financial":
        return "The clause creates monetary exposure or cost escalation risk."
    if category == "Payment":
        return "The clause imposes payment or compensation obligations."
    if category == "Timeline":
        return "The clause enforces delivery timelines that may trigger delays."
    if category == "Legal":
        return "The clause introduces legal liability or enforcement risk."
    if category == "Resource":
        return "The clause imposes manpower or operational obligations."
    return "The clause introduces contractual risk."


# ======================================================
# MAIN ENTRY POINT (SENTENCE-LEVEL RISKS)
# ======================================================
def analyze_pdf(uploaded_file):
    text = extract_text(uploaded_file)
    clauses = split_clauses(text)

    ai_candidates = [c for c in clauses if requires_ai_analysis(c)]
    classified = classify_clauses_batch(ai_candidates)

    results = []
    seen = set()  # prevent exact duplicates

    for clause, primary_category, confidence in classified:

        # 🔑 SPLIT INTO SENTENCES = MULTIPLE RISKS PER CATEGORY
        sentences = re.split(r"(?<=[.;])\s+", clause)

        for sentence in sentences:
            sentence = sentence.strip()

            if len(sentence) < 50:
                continue

            categories = expand_related_risks(primary_category, sentence)

            for category in categories:
                key = (category, sentence)
                if key in seen:
                    continue
                seen.add(key)

                severity, status = severity_from_confidence(confidence or 0.6, sentence)

                results.append({
                    "category": category,
                    "clause": sentence[:90] + ("..." if len(sentence) > 90 else ""),
                    "content": sentence,
                    "severity": severity,
                    "status": status,
                    "impact": generate_ai_impact(category, sentence),
                    "tag_class": f"tag-{category.lower()}"
                })

    if not results:
        return [{
            "category": "Financial",
            "clause": "Bid eligibility and administrative conditions detected",
            "content": "The document mainly contains eligibility and administrative requirements.",
            "severity": 40,
            "status": "Warning",
            "impact": "Risk analysis is more effective on final contract or SLA documents.",
            "tag_class": "tag-financial"
        }]

    STATUS_WEIGHT = {"Critical": 3, "Warning": 2, "Low": 1}

    def risk_score(r):
        return r["severity"] * 1.5 + STATUS_WEIGHT.get(r["status"], 1) * 20

    results.sort(key=risk_score, reverse=True)

    # Return ONLY top 10 risks as a list
    return results[:10]

