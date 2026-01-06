import pdfplumber
import re

# -----------------------------
# Risk Configuration
# -----------------------------
RISK_RULES = {
    "Financial": ["liquidated damages", "penalty", "retention", "price escalation"],
    "Payment": ["payment", "net", "invoice", "credit period"],
    "Legal": ["indemnity", "termination", "liability", "force majeure"],
    "Timeline": ["delay", "timeline", "completion", "milestone"],
    "Resource": ["manpower", "staff", "equipment"]
}

# -----------------------------
# PDF TEXT EXTRACTION
# -----------------------------
def extract_text(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


# -----------------------------
# CLAUSE SPLITTING
# -----------------------------
def split_clauses(text):
    clauses = re.split(r"\n(?=\d+\.|\bClause\b|\bSection\b)", text)
    return [c.strip() for c in clauses if len(c.strip()) > 80]


# -----------------------------
# SEVERITY LOGIC (Deterministic)
# -----------------------------
def calculate_severity(text, hits):
    base = 30
    length_score = min(len(text) / 400, 1.5) * 20
    keyword_score = hits * 15
    return min(int(base + length_score + keyword_score), 95)


# -----------------------------
# MAIN ANALYSIS FUNCTION
# -----------------------------
def analyze_pdf(uploaded_file):
    text = extract_text(uploaded_file)
    clauses = split_clauses(text)

    results = []

    for clause in clauses:
        clause_lower = clause.lower()

        for category, keywords in RISK_RULES.items():
            hits = sum(1 for k in keywords if k in clause_lower)
            if hits > 0:
                severity = calculate_severity(clause, hits)
                status = (
                    "Critical" if severity >= 75
                    else "Warning" if severity >= 45
                    else "Low"
                )

                results.append({
                    "category": category,
                    "clause": clause[:70] + "...",
                    "content": clause,
                    "severity": severity,
                    "status": status,
                    "impact": f"Identified using {category} risk indicators and tender standards.",
                    "tag_class": f"tag-{category.lower()}"
                })

    return results
