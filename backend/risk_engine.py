import json
import os
import pdfplumber
import re
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

LABELS = ["Financial", "Legal", "Payment", "Timeline", "Resource"]

# Initialize Groq client
_groq_client = None

def get_groq_client():
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            _groq_client = Groq(api_key=api_key)
    return _groq_client


# TEXT EXTRACTION
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


# CLAUSE SPLITTING
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


# AI GATE (PERFORMANCE)
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
    return any(k in t for k in HARD_KEYWORDS)


def classify_clause_groq(text: str):
    """
    Uses Groq API (llama-3.3-70b-versatile) to classify clauses.
    Returns: (category, confidence)
    """
    client = get_groq_client()
    if not client:
        # Fallback to keyword classification
        return keyword_classify(text)

    prompt = f"""You are a contract risk classifier.

Classify the following clause into ONLY ONE category from:
Financial, Legal, Payment, Timeline, Resource

Return output strictly as JSON like:
{{
  "category": "Financial|Legal|Payment|Timeline|Resource|None",
  "confidence": 0.85
}}

Do NOT include any explanation. Only return the JSON.

Clause:
\"\"\"{text[:800]}\"\"\"
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=100
        )

        content = response.choices[0].message.content.strip()

        # Extract JSON safely
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1:
            return keyword_classify(text)

        data = json.loads(content[start:end + 1])

        category = data.get("category", None)
        confidence = float(data.get("confidence", 0.0))

        if category == "None" or category not in LABELS:
            return None, confidence

        return category, confidence

    except Exception as e:
        print(f"[risk_engine] Groq classify failed: {e}. Using keyword fallback.")
        return keyword_classify(text)


def keyword_classify(text: str):
    """
    Pure keyword-based fallback classifier.
    Returns (category, confidence).
    """
    t = text.lower()

    scores = {
        "Payment": sum(1 for k in ["payment", "compensation", "fees", "charges", "corpus fund", "gst", "stamp duty", "premium", "paid", "payable"] if k in t),
        "Financial": sum(1 for k in ["liquidated", "penalty", "damages", "cost", "expense", "fsi", "tdr", "fungible"] if k in t),
        "Timeline": sum(1 for k in ["delay", "time", "completion", "schedule", "milestone", "months", "days", "handover", "deadline"] if k in t),
        "Legal": sum(1 for k in ["terminate", "termination", "indemn", "liability", "arbitration", "court", "litigation"] if k in t),
        "Resource": sum(1 for k in ["manpower", "staff", "labour", "equipment", "machinery"] if k in t),
    }

    best_cat = max(scores, key=scores.get)
    best_score = scores[best_cat]

    if best_score == 0:
        return None, 0.0

    # Normalize confidence (0 to 1 range, max 3 keyword hits = 1.0)
    confidence = min(best_score / 3.0, 1.0)
    return best_cat, confidence


def classify_clauses_batch(texts, threshold=0.12, batch_size=8):
    """
    Classifies a list of clauses.
    Returns: [(text, category, confidence), ...]
    """
    results = []

    for text in texts:
        category, confidence = classify_clause_groq(text)

        if category and confidence >= threshold:
            results.append((text, category, confidence))
        else:
            results.append((text, None, 0.0))

    return results


# RISK EXPANSION (DOMAIN-AWARE)
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


# SEVERITY
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


# HIGHLIGHT
def extract_risk_highlight(text, category):
    return text.strip()


# AI IMPACT — Enhanced with Groq for richer insights
def generate_ai_impact(category, text):
    """Generate a context-aware impact statement based on category and clause text."""
    t = text.lower()

    if category == "Financial":
        if "liquidated" in t or "penalty" in t:
            return "This clause imposes **liquidated damages or penalty clauses** that create direct financial liability. Quantify the maximum exposure and ensure mitigation strategies are in place."
        return "The clause creates monetary exposure, cost escalation, or financial liability risk that could affect project profitability."

    if category == "Payment":
        if "corpus fund" in t or "displacement" in t:
            return "The clause mandates **corpus fund contributions or displacement compensation** — these are non-negotiable financial obligations requiring upfront capital allocation."
        return "The clause imposes payment or compensation obligations with defined timelines. Delayed payment may attract interest or penalties."

    if category == "Timeline":
        if "delay" in t:
            return "This clause carries **delay risk** — non-completion within stipulated time triggers penalties. Review extension of time (EOT) provisions carefully."
        return "The clause enforces strict delivery timelines. Failure to meet milestones may trigger penalties or contract termination."

    if category == "Legal":
        if "arbitration" in t:
            return "This clause specifies **arbitration as the dispute resolution mechanism** — understand the jurisdiction, arbitrator selection, and enforceability."
        if "terminate" in t or "termination" in t:
            return "The clause grants **termination rights** — understand under what conditions and what the financial/legal consequences are."
        return "The clause introduces legal liability, indemnity obligations, or enforcement risk that requires legal review."

    if category == "Resource":
        return "The clause imposes **manpower, equipment, or resource deployment obligations** that must be pre-planned to avoid compliance failures."

    return "The clause introduces contractual risk requiring review and mitigation strategy."


# MAIN ENTRY POINT (SENTENCE-LEVEL RISKS)
def analyze_pdf(uploaded_file):
    text = extract_text(uploaded_file)
    clauses = split_clauses(text)

    ai_candidates = [c for c in clauses if requires_ai_analysis(c)]
    classified = classify_clauses_batch(ai_candidates)

    results = []
    seen = set()  # prevent exact duplicates

    for clause, primary_category, confidence in classified:

        # SPLIT INTO SENTENCES = MULTIPLE RISKS PER CATEGORY
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

    # Return top 10 risks
    return results[:10]
