import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import json
import xgboost as xgb
import re
import os
from typing import Optional
from PyPDF2 import PdfReader
from supabase import create_client
from dotenv import load_dotenv
import base64
from pathlib import Path
from utils.auth import can_access

def get_base64_of_bin_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

if "strategy_saved" not in st.session_state:
    st.session_state.strategy_saved = False


# --- 1. PAGE CONFIGURATION (MUST BE FIRST) ---
st.set_page_config(
    page_title="TenderFlow | AI Bid Suite",
    layout="wide",
    initial_sidebar_state="collapsed"
)
if not os.getenv("GROQ_API_KEY"):
    st.warning("Groq API key not found. Using keyword-based material detection only.")
# --- 2. INITIALIZATION & SESSION STATE ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Session State Keys (Logic from original code)
if "extraction_done" not in st.session_state:
    st.session_state.extraction_done = False

if "tender_data" not in st.session_state:
    st.session_state.tender_data = None

if "complexity_score" not in st.session_state:
    st.session_state.complexity_score = None 

if "cost_df" not in st.session_state:
    st.session_state.cost_df = pd.DataFrame(
        columns=["Task", "Qty", "Rate"]
    )
    
MATERIAL_KEYWORDS = [
    "cement", "steel", "reinforcement", "bitumen", "asphalt",
    "aggregate", "sand", "brick", "blocks", "concrete",
    "pcc", "rcc", "cable", "wire", "pipe", "valve",
    "transformer", "panel", "switchgear", "battery",
    "server", "router", "switch", "hardware",
    "excavation", "earthwork", "granular", "wmm"
]

DEFAULT_MATERIAL_RATES = {
    "cement": 420,          # per bag
    "steel": 62000,         # per MT
    "reinforcement": 65000,
    "sand": 1800,           # per brass
    "aggregate": 1500,
    "bitumen": 55000,
    "brick": 9,             # per brick
    "concrete": 6500        # per cum
}

NON_BILLABLE_KEYWORDS = [
    "conditions",
    "specification",
    "approved makes",
    "scope of work",
    "instructions",
    "eligibility",
    "criteria",
    "checklist",
    "formats",
    "annexure",
    "schedule of completion"
]

# Supabase Setup
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase credentials not found. Check your .env file.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Try to import custom utility (Logic from original code)
try:
    from utils.complexity import compute_complexity_score
except ImportError:
    def compute_complexity_score(file):
        return 5  # default fallback

@st.cache_resource
def load_model():
    try:
        import pickle
        # Load XGBClassifier from pkl (supports predict_proba)
        with open("ml/tenderflow_xgboost.pkl", "rb") as f:
            model = pickle.load(f)
        with open("ml/feature_columns.json") as f:
            features = json.load(f)
        return model, features
    except Exception:
        # Fallback: try loading from JSON with XGBClassifier
        try:
            model = xgb.XGBClassifier()
            model.load_model("ml/tenderflow_xgboost.json")
            with open("ml/feature_columns.json") as f:
                features = json.load(f)
            return model, features
        except Exception:
            return None, None

model, FEATURE_COLUMNS = load_model()

# --- 3. HELPERS (Original Logic) ---
def format_inr(number):
    """Formats a number into Indian System (Lakhs/Crores). Safe for all values."""
    try:
        number = float(number)
        if number < 0:
            return "-" + format_inr(-number)
        s, *d = str(f"{number:.2f}").partition(".")
        # Indian grouping: last 3 digits, then groups of 2
        if len(s) <= 3:
            r = s
        else:
            r = s[-3:]
            s = s[:-3]
            while s:
                r = s[-2:] + "," + r
                s = s[:-2]
        return "₹" + r + "".join(d)
    except Exception:
        return f"₹{number:,.2f}"
    
def safe_json_parse(text):
    try:
        return json.loads(text)
    except:
        match = re.search(r"\[[\s\S]*?\]", text)
        if match:
            try:
                return json.loads(match.group())
            except:
                return []
        return []

def classify_item(task_name: str) -> str:
    t = task_name.lower()

    for kw in NON_BILLABLE_KEYWORDS:
        if kw in t:
            return "non_billable"

    for kw in MATERIAL_KEYWORDS:
        if kw in t:
            return "material"

    return "service"

def normalize_task(task: str) -> str:
    task = task.lower()
    for kw in MATERIAL_KEYWORDS:
        if kw in task:
            return kw.title()
    return task.title()

def keyword_fallback_items(text):
    found = set()
    t = text.lower()

    for kw in MATERIAL_KEYWORDS:
        if kw in t:
            found.add(kw.title())

    return [
        {"Task": item, "Qty": 1, "Rate": 0}
        for item in sorted(found)
    ]
    
def extract_billable_items(text):
    if not os.getenv("GROQ_API_KEY"):
        st.warning("Groq API key missing")
        return []

    prompt = f"""
You are a specialized tender BOQ (Bill of Quantities) extraction engine for Indian government and infrastructure projects.

From the tender document text below, extract ALL billable or quote-required line items.

Include:
- BOQ headings and schedule items
- Commercial bid items
- Compensation / payment line items
- Service fees, charges, or deliverables with a monetary component
- Supply items, materials, equipment

Strict Rules:
- Each item: SHORT heading only (3-12 words), no quantities, no rates, no explanations
- Skip eligibility criteria, conditions of contract, general instructions, annexures
- Output ONLY a valid JSON array of strings
- Do NOT include any text before or after the JSON array
- Maximum 30 items
- If no clear BOQ items found, return an empty array: []

EXAMPLE:
[
  "Hardship compensation lump sum amount",
  "Monthly displacement compensation per family",
  "Stamp duty and registration charges",
  "RCC column construction per floor",
  "Electrical panel supply and installation"
]

TENDER TEXT (first 4000 chars):
{text[:4000]}

JSON ARRAY OUTPUT:
"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a BOQ extraction engine. Always return only a valid JSON array. Never explain anything."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0,
                "max_tokens": 1024
            },
            timeout=30
        )

        data = response.json()

        if "choices" not in data:
            error_msg = data.get("error", {}).get("message", "Unknown Groq error")
            st.error(f"Groq error: {error_msg}")
            return []
        
        raw = data["choices"][0]["message"]["content"]
        items = safe_json_parse(raw)

        if not isinstance(items, list):
            return []

        return [
            {"Task": normalize_task(item), "Qty": 1, "Rate": 0}
            for item in items
            if isinstance(item, str) and item.strip()
        ]

    except Exception as e:
        st.error(f"Groq failed: {e}")
        return []

def auto_fill_rates(boq_items, tender_text):
    if not os.getenv("GROQ_API_KEY"):
        return boq_items

    priced_items = []

    for item in boq_items:
        task = item["Task"]
        item_type = classify_item(task)

        # Use default rates for known materials to avoid expensive API calls
        task_lower = task.lower()
        default_rate = None
        for mat_key, mat_rate in DEFAULT_MATERIAL_RATES.items():
            if mat_key in task_lower:
                default_rate = mat_rate
                break

        if default_rate is not None:
            priced_items.append({"Task": task, "Qty": 1, "Rate": default_rate})
            continue

        category_hint = {
            "material": "raw material or construction supply",
            "service": "professional service or labour work",
            "non_billable": "administrative or documentation item"
        }.get(item_type, "general item")

        prompt = f"""You are an Indian procurement and tender costing expert specializing in government projects.

Determine a realistic Indian local market rate for the item below.

Context:
- Item Type: {category_hint}
- Year: 2024-2025
- Market: Indian government/PSU procurement

Rules:
- Rate MUST be a single number in INR
- Assume quantity = 1 unit
- For services: per day/lump sum as appropriate
- For materials: per standard unit (kg, MT, cum, bag, etc.)
- NO ranges, NO explanation, NO units in the number
- If item is non-billable or administrative, return 0
- Return STRICT JSON only: {{"rate": 12345}}

Item: "{task}"

Tender context (scale reference only):
{tender_text[:800]}

JSON:
"""

        rate = 0

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "You are a pricing engine. Return only valid JSON with a single 'rate' key."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 50
                },
                timeout=15
            )

            data = response.json()
            if "choices" in data:
                raw = data["choices"][0]["message"]["content"]
                parsed = safe_json_parse(raw)
                if isinstance(parsed, dict) and "rate" in parsed:
                    rate = int(parsed["rate"])

        except Exception:
            rate = 0

        priced_items.append({
            "Task": task,
            "Qty": 1,
            "Rate": rate
        })

    return priced_items

# High-risk material keywords that increase material_risk_score
_HIGH_RISK_MATERIALS = [
    "bitumen", "asphalt", "transformer", "cable", "switchgear", "panel",
    "pile", "reinforcement", "rcc", "pcc", "excavation", "earthwork"
]

def _compute_boq_context(boq_df: pd.DataFrame) -> dict:
    """
    Derive tender-specific context factors from the BOQ dataframe.
    Returns a dict of normalized (0→1) signals.
    """
    if boq_df is None or boq_df.empty:
        return {"material_risk": 0.0, "item_density": 0.0, "scope_breadth": 0.0}

    task_names = " ".join(boq_df["Task"].astype(str).str.lower().tolist())
    item_count = len(boq_df)

    # Count how many high-risk material keywords appear in all task names
    risk_hits = sum(1 for kw in _HIGH_RISK_MATERIALS if kw in task_names)
    material_risk = min(risk_hits / max(len(_HIGH_RISK_MATERIALS), 1), 1.0)

    # Item density: more items = broader scope = slightly more risk (harder to win)
    item_density = min(item_count / 30.0, 1.0)

    # Scope breadth: ratio of unique categories (material vs service vs non-billable)
    categories = set(classify_item(t) for t in boq_df["Task"].astype(str))
    scope_breadth = min(len(categories) / 3.0, 1.0)

    return {
        "material_risk": material_risk,
        "item_density": item_density,
        "scope_breadth": scope_breadth,
    }


def _predict_pure(
    prime_cost: float,
    overhead_pct: float,
    profit_pct: float,
    estimated_budget: float,
    complexity_score: float,
    competitors: int,
    boq_context: Optional[dict] = None,
) -> float:
    """
    Pure, side-effect-free win probability calculation.
    Dynamic per tender via boq_context. Used internally by the AI optimizer loop.

    Factors (weighted):
      40% — price-to-budget ratio (bell-curve peak at 0.80 of budget)
      18% — profit margin impact
      17% — competitor density
      10% — tender complexity
       7% — material risk (high-risk materials in BOQ)
       5% — BOQ item count (denser tender = harder to win)
       3% — scope breadth (multi-category = marginally harder)
    """
    ctx = boq_context or {"material_risk": 0.0, "item_density": 0.0, "scope_breadth": 0.0}

    # ── 1. Price-to-budget score (bell curve peaked at 80% of budget) ──────────
    bid_price = prime_cost * (1 + overhead_pct / 100) * (1 + profit_pct / 100)
    budget_safe = max(estimated_budget, 1.0)
    price_ratio = bid_price / budget_safe

    if price_ratio <= 0.80:
        # Under 80% of budget: strong but not artificially high
        price_score = 0.82 + price_ratio * 0.225  # linear ramp 0 → 0.80 gives 0.82 → 1.00
    elif price_ratio <= 1.0:
        # 80% – 100% of budget: excellent zone
        price_score = 1.0 - (price_ratio - 0.80) * 0.55  # slight decline toward limit
    elif price_ratio <= 1.15:
        # Just over budget: steep decline
        price_score = max(0.0, 0.89 - (price_ratio - 1.0) * 4.0)
    else:
        # Far over budget: near zero
        price_score = max(0.0, 0.29 - (price_ratio - 1.15) * 1.5)
    price_score = min(max(price_score, 0.0), 1.0)

    # ── 2. Profit margin score ──────────────────────────────────────────────────
    # Logistic-style: profits above 20% drop off steeply
    if profit_pct <= 15:
        profit_score = 1.0 - profit_pct * 0.018
    else:
        profit_score = (1.0 - 15 * 0.018) - (profit_pct - 15) * 0.042
    profit_score = min(max(profit_score, 0.0), 1.0)

    # ── 3. Competitor density score ─────────────────────────────────────────────
    competition_score = 1.0 / (1.0 + competitors * 0.22)

    # ── 4. Complexity score (higher complexity = harder to win) ─────────────────
    complexity_penalty = complexity_score / 10.0
    complexity_score_norm = 1.0 - min(complexity_penalty, 1.0)

    # ── 5. Material risk (tender-specific) ─────────────────────────────────────
    # High-risk materials (cables, bitumen, piles…) increase execution risk
    material_risk_penalty = ctx["material_risk"] * 0.4   # at worst cuts this signal by 40%
    material_score = 1.0 - material_risk_penalty

    # ── 6. Item density (tender-specific) ─────────────────────────────────────
    item_score = 1.0 - ctx["item_density"] * 0.5

    # ── 7. Scope breadth (tender-specific) ─────────────────────────────────────
    breadth_score = 1.0 - ctx["scope_breadth"] * 0.25

    # ── Weighted sum ────────────────────────────────────────────────────────────
    base_prob = (
        price_score      * 0.40 +
        profit_score     * 0.18 +
        competition_score * 0.17 +
        complexity_score_norm * 0.10 +
        material_score   * 0.07 +
        item_score       * 0.05 +
        breadth_score    * 0.03
    )

    # ── ML model blend ─────────────────────────────────────────────────────────
    ml_prob = None
    if model is not None and FEATURE_COLUMNS is not None:
        try:
            input_data = {
                "prime_cost": prime_cost,
                "overhead_pct": overhead_pct,
                "profit_pct": profit_pct,
                "estimated_budget": estimated_budget,
                "complexity_score": complexity_score,
                "competitor_density": competitors
            }
            df_input = pd.DataFrame([input_data])
            for col in FEATURE_COLUMNS:
                if col not in df_input.columns:
                    df_input[col] = 0
            df_input = df_input[FEATURE_COLUMNS]
            ml_prob = float(model.predict_proba(df_input)[0][1])
        except Exception:
            ml_prob = None

    if ml_prob is not None:
        final_prob = ml_prob * 0.55 + base_prob * 0.45
    else:
        final_prob = base_prob

    return min(max(final_prob, 0.05), 0.95)


def predict_win_probability(
    prime_cost: float,
    overhead_pct: float,
    profit_pct: float,
    estimated_budget: float,
    complexity_score: float,
    competitors: int,
    boq_context: Optional[dict] = None,
) -> float:
    """
    Public function for the UI — calls _predict_pure (no session-state writes).
    """
    return _predict_pure(
        prime_cost=prime_cost,
        overhead_pct=overhead_pct,
        profit_pct=profit_pct,
        estimated_budget=estimated_budget,
        complexity_score=complexity_score,
        competitors=competitors,
        boq_context=boq_context,
    )

def bid_generation_page():
    if not st.session_state.get("authenticated"):
        st.error("Please login to continue.")
        st.stop()

    if not st.session_state.get("active_company_id"):
        st.error("Company context missing. Please login again.")
        st.stop()
        
    # --- PREMIUM UI STYLES ---
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap');


/* ── Global ─────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp {
    background: radial-gradient(ellipse 120% 80% at 18% 25%, #1e1b4b 0%, #0c0a1d 55%, #030014 100%) !important;
}
header, footer { visibility: hidden; }
div.block-container {
    padding-top: 0.4rem !important;
    padding-bottom: 2rem !important;
}
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(168,85,247,0.35); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(168,85,247,0.6); }

/* ── Label ──────────────────────────────────────── */
.label-text {
    color: rgba(168,85,247,0.65) !important;
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ── Buttons ────────────────────────────────────── */
.stButton>button {
    width: 100%;
    border-radius: 14px !important;
    border: none !important;
    background: linear-gradient(135deg, #7c3aed 0%, #a855f7 50%, #c084fc 100%) !important;
    color: white !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    padding: 0.65rem 1rem !important;
    box-shadow: 0 4px 18px rgba(124,58,237,0.25) !important;
    transition: all 0.25s cubic-bezier(.4,0,.2,1) !important;
}
.stButton>button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 28px rgba(124,58,237,0.38) !important;
}
.stButton>button:active { transform: translateY(0px) scale(0.99) !important; }
.stButton>button:disabled { opacity: 0.45 !important; box-shadow: none !important; }

/* ── Inputs ─────────────────────────────────────── */
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 14px !important;
    color: #f4f4f5 !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border: 1px solid rgba(168,85,247,0.50) !important;
    box-shadow: 0 0 0 3px rgba(168,85,247,0.12) !important;
}

/* ── Sliders ────────────────────────────────────── */
.stSlider label, .stSelectSlider label {
    font-weight: 600 !important;
    color: rgba(244,244,245,0.55) !important;
    font-size: 12px !important;
}
div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
    background-color: #fff !important;
    border: 2px solid #fff !important;
    box-shadow: 0 0 0 4px rgba(168,85,247,0.18) !important;
}
div[data-testid="stSlider"] [data-baseweb="slider"] div > div > div {
    background-color: #a855f7 !important;
    border-radius: 10px;
}

/* ── Data Editor ────────────────────────────────── */
div[data-testid="stDataFrame"] {
    border-radius: 16px !important;
    overflow: hidden !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    box-shadow: 0 8px 25px rgba(0,0,0,0.25);
}
div[data-testid="stDataFrame"] * { font-size: 0.88rem !important; }

/* ── File Uploader ──────────────────────────────── */
[data-testid="stFileUploadDropzone"] {
    background: rgba(168,85,247,0.04) !important;
    border: 2px dashed rgba(168,85,247,0.30) !important;
    border-radius: 16px !important;
    transition: all 0.2s ease !important;
}
[data-testid="stFileUploadDropzone"]:hover {
    background: rgba(168,85,247,0.08) !important;
    border-color: rgba(168,85,247,0.50) !important;
}

/* ── Containers ─────────────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: rgba(255,255,255,0.07) !important;
    border-radius: 18px !important;
    background: rgba(255,255,255,0.015) !important;
}

/* ── Alerts ─────────────────────────────────────── */
.stAlert {
    border-radius: 14px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    background: rgba(255,255,255,0.04) !important;
    backdrop-filter: blur(8px);
}

/* ── Divider ────────────────────────────────────── */
hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, rgba(168,85,247,0.30), transparent) !important;
    margin: 12px 0 18px 0 !important;
}

/* ── Select box labels ──────────────────────────── */
.stSelectbox label {
    color: rgba(255,255,255,0.45) !important;
    font-size: 10.5px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ── Bid Box (Hero Card) ────────────────────────── */
.bid-box {
    background: linear-gradient(135deg, rgba(124,58,237,0.30) 0%, rgba(15,17,26,0.90) 55%, rgba(168,85,247,0.15) 100%);
    border-radius: 24px;
    padding: 32px 28px 28px;
    text-align: center;
    box-shadow: 0 20px 50px rgba(124,58,237,0.18);
    border: 1px solid rgba(168,85,247,0.25);
    position: relative;
    overflow: hidden;
}
.bid-box::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #7c3aed, #a855f7, #c084fc, #a855f7, #7c3aed);
}
.bid-box::after {
    content: '';
    position: absolute;
    width: 350px; height: 350px;
    top: -220px; left: -200px;
    background: radial-gradient(circle, rgba(168,85,247,0.25) 0%, transparent 65%);
    pointer-events: none;
}
.bid-price {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 2.8rem;
    font-weight: 700;
    color: #fff !important;
    letter-spacing: -1.5px;
    margin: 8px 0;
    position: relative;
    z-index: 1;
}

/* ── Metrics Grid ───────────────────────────────── */
.tf-metric-grid {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 8px 18px;
    margin-top: 12px;
    padding: 18px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.025);
}
.tf-metric-label {
    font-size: 0.82rem;
    font-weight: 600;
    color: rgba(244,244,245,0.50) !important;
}
.tf-metric-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: #f4f4f5 !important;
    font-family: 'JetBrains Mono', monospace !important;
    text-align: right;
}
.tf-metric-highlight {
    grid-column: 1 / -1;
    text-align: center;
    margin-top: 8px;
    padding-top: 12px;
    border-top: 1px solid rgba(168,85,247,0.18);
    font-size: 0.82rem;
    font-weight: 700;
    color: #c084fc !important;
}

a { color: #a855f7 !important; text-decoration: none !important; }
a:hover { text-decoration: underline !important; }

</style>
""", unsafe_allow_html=True)

    # HEADER
    left, center = st.columns([3, 6])

    with left:
        logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
        logo = get_base64_of_bin_file(logo_path)
        if logo:
            st.markdown(f'<img src="data:image/png;base64,{logo}" width="180" style="margin-top:4px">', unsafe_allow_html=True)

    with center:
        header_cols = st.columns([3, 0.5, 0.5, 0.5, 0.5, 0.5])

        with header_cols[1]:
            if st.button("⊞", key="h_dash", help="Dashboard"):
                st.switch_page("app.py")
        with header_cols[2]:
            if can_access("tender_generation"):
                if st.button("⎘", key="h_gen", help="Tender Generation"):
                    st.switch_page("pages/tenderGeneration.py")
            else:
                st.button("⎘", key="h_gen_disabled", disabled=True)
        with header_cols[3]:
            if can_access("tender_analysis"):
                if st.button("◈", key="h_anl", help="Tender Analysis"):
                    st.switch_page("pages/tenderAnalyser.py")
            else:
                st.button("◈", key="h_anl_disabled", disabled=True)
        with header_cols[4]:
            if can_access("bid_generation"):
                if st.button("✦", key="h_bid", help="Bid Generation"):
                    st.switch_page("pages/bidGeneration.py")
            else:
                st.button("✦", key="h_bid_disabled", disabled=True)
        with header_cols[5]:
            if can_access("risk_analysis"):
                if st.button("⬈", key="h_risk", help="Risk Analysis"):
                    st.switch_page("pages/riskAnalysis.py")
            else:
                st.button("⬈", key="h_risk_disabled", disabled=True)

    # PAGE TITLE
    st.markdown("""
    <div style="
        display:flex;justify-content:space-between;align-items:center;
        margin:8px 0 22px;padding:22px 28px;
        background:linear-gradient(135deg, rgba(124,58,237,0.10) 0%, rgba(168,85,247,0.05) 50%, rgba(255,255,255,0.015) 100%);
        border:1px solid rgba(168,85,247,0.15);border-radius:22px;
        backdrop-filter:blur(10px);position:relative;overflow:hidden;
    ">
        <div style="position:relative;z-index:1;">
            <h1 style="font-size:2rem;font-weight:900;background:linear-gradient(135deg,#fff 0%,#e9d5ff 40%,#c084fc 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;letter-spacing:-0.5px;">Bid Generation</h1>
            <p style="color:rgba(255,255,255,0.42);font-size:12.5px;margin:4px 0 0;font-weight:500;">Smart Bid Optimization &amp; Win Probability Engine</p>
        </div>
        <div style="position:relative;z-index:1;display:inline-block;padding:6px 16px;border:1px solid rgba(168,85,247,0.30);border-radius:100px;background:rgba(168,85,247,0.10);color:#c084fc;font-size:11px;font-weight:700;letter-spacing:0.5px;">AI Powered</div>
    </div>
    """, unsafe_allow_html=True)

    # UPLOAD PANEL
    if not st.session_state.extraction_done:
        st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)
        _, col_mid, _ = st.columns([1, 1.6, 1])
        with col_mid:
            st.markdown("""
            <div style="text-align:center;margin-bottom:28px;">
                <div style="font-size:52px;margin-bottom:12px;filter:drop-shadow(0 4px 12px rgba(168,85,247,0.3));">📂</div>
                <h2 style="font-size:22px;font-weight:800;background:linear-gradient(135deg,#fff,#e9d5ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0 0 6px;">Initialize New Bid</h2>
                <p style="color:rgba(255,255,255,0.42);font-size:13px;margin:0;">Upload your tender PDF to begin AI-powered cost extraction</p>
            </div>
            """, unsafe_allow_html=True)
            with st.container(border=True):
                uploaded_tender = st.file_uploader(
                    "Drop PDF here",
                    type=["pdf"],
                    label_visibility="collapsed"
                )

            if uploaded_tender:
                file_id = f"{uploaded_tender.name}_{uploaded_tender.size}"

                # Skip if already processed this exact file
                if st.session_state.get("processed_file") == file_id and st.session_state.extraction_done:
                    return  # Already done, dashboard will show
                
                # Skip if currently analyzing (prevents rerun loop)
                if st.session_state.get("analyzing_file") == file_id:
                    st.info("🔮 Analysis in progress...")
                    return
                    
                # Reset strategy_saved flag when a new file is detected
                if st.session_state.get("last_file") != uploaded_tender.name:
                    st.session_state.last_file = uploaded_tender.name
                    st.session_state.cost_df = pd.DataFrame(columns=["Task", "Qty", "Rate"])
                    st.session_state.extraction_done = False
                    st.session_state.processed_file = None
                    st.session_state.strategy_saved = False  # Reset save flag for new file
                
                # Mark as analyzing to prevent duplicate runs
                st.session_state.analyzing_file = file_id
                
                with st.spinner("🔮 Analyzing tender…"):
                    try:
                        reader = PdfReader(uploaded_tender)
                        text = " ".join([p.extract_text() or "" for p in reader.pages])
                        
                        # 1️⃣ AI extraction
                        boq_items = extract_billable_items(text)

                        # 2️⃣ Keyword fallback if AI fails
                        if not boq_items:
                            st.warning("AI BOQ extraction failed. Using keyword-based detection.")
                            boq_items = keyword_fallback_items(text)

                        # 3️⃣ Final manual fallback
                        if not boq_items:
                            boq_items = [{"Task": "Add item manually", "Qty": 1, "Rate": 0}]

                        # 4️⃣ Auto-fill rates ONLY if we have items
                        boq_items = auto_fill_rates(boq_items, text)

                        st.session_state.cost_df = pd.DataFrame(boq_items)
                        
                        def extract_amount(label):
                            """
                            Extract rupee amounts from tender text. Handles:
                            - ₹ symbol and Rs./Rs variations
                            - Lakhs (e.g., 12,50,000 or 12.50 Lakhs)
                            - Crores notation
                            """
                            # Try ₹ symbol first
                            patterns = [
                                rf"(?:{label})[^\n]{{0,80}}₹\s*([\d,\.]+)\s*(Lakh|Crore|lakh|crore|L|Cr)?",
                                rf"(?:{label})[^\n]{{0,80}}Rs\.?\s*([\d,\.]+)\s*(Lakh|Crore|lakh|crore|L|Cr)?",
                                rf"(?:{label})[^\n]{{0,80}}INR\s*([\d,\.]+)\s*(Lakh|Crore|lakh|crore|L|Cr)?",
                                rf"([\d,\.]+)\s*(Lakh|Crore|lakh|crore|L|Cr)[^\n]{{0,60}}(?:{label})",
                            ]
                            for pat in patterns:
                                m = re.search(pat, text, re.IGNORECASE)
                                if m:
                                    try:
                                        val_str = m.group(1).replace(",", "")
                                        val = float(val_str)
                                        unit = (m.group(2) or "").lower()
                                        if unit in ("lakh", "l"):
                                            val *= 100000
                                        elif unit in ("crore", "cr"):
                                            val *= 10000000
                                        return val
                                    except (IndexError, ValueError):
                                        continue
                            return 0.0

                        tender_data = {
                            "estimated_budget": extract_amount("Estimated Cost|Tender Value|Estimated Amount|Approximate Value|Total Estimated"),
                            "emd": extract_amount("EMD|Earnest Money"),
                        }

                        complexity_score = compute_complexity_score(uploaded_tender)

                        st.session_state.tender_data = tender_data
                        st.session_state.complexity_score = int(complexity_score)

                        # Original Database Logic
                        res = supabase.table("tenders").insert({
                            "authority_name": uploaded_tender.name,
                            "estimated_budget": tender_data["estimated_budget"],
                            "complexity_score": int(complexity_score),
                        }).execute()
                        tender_id = res.data[0]["id"]
                        st.session_state.tender_id = tender_id
                        
                        # Mark as completed
                        st.session_state.processed_file = file_id
                        st.session_state.analyzing_file = None
                        st.session_state.extraction_done = True
                        st.rerun()
                        
                    except Exception as e:
                        st.session_state.analyzing_file = None  # Clear on error
                        st.error(f"Analysis failed: {str(e)}")
            st.markdown('</div>', unsafe_allow_html=True)
        return

    # DASHBOARD - POST-EXTRACTION
    tender_data = st.session_state.tender_data or {}
    complexity_score = st.session_state.complexity_score or 5

    left_col, right_col = st.columns([1.8, 1.2], gap="large")

    with left_col:
        st.markdown('<p class="label-text">📋 Bill of Quantities (BOQ)</p>', unsafe_allow_html=True)
        st.caption("🤖 Items extracted by AI. Verify quantities & rates before submitting.")
        
        edited_df = st.data_editor(
            st.session_state.cost_df,
            key="bid_cost_editor",
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Rate": st.column_config.NumberColumn(format="₹%d"), 
                "Qty": st.column_config.NumberColumn(step=1),
            }
        )
        edited_df["Qty"] = pd.to_numeric(edited_df["Qty"], errors="coerce").fillna(0)
        edited_df["Rate"] = pd.to_numeric(edited_df["Rate"], errors="coerce").fillna(0)
        total_prime = (edited_df["Qty"] * edited_df["Rate"]).sum()

        st.session_state.cost_df = edited_df

        # Compute BOQ context once per render (used for dynamic prediction)
        boq_context = _compute_boq_context(edited_df)

        multiplier = st.slider("Estimated Client Budget Multiplier", 1.05, 1.8, 1.3, 0.05)

        # Use PDF-extracted budget only when it's a valid non-zero value;
        # otherwise fall back to prime cost × multiplier so win probability isn't broken.
        pdf_budget = tender_data.get("estimated_budget") or 0.0
        budget_source = "PDF"
        if pdf_budget and pdf_budget > 0:
            estimated_budget = pdf_budget
        else:
            estimated_budget = max(total_prime * multiplier, 1.0)
            budget_source = "AI-Estimated"

        budget_col1, budget_col2 = st.columns(2)
        with budget_col1:
            st.markdown(
                f"<div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:16px 18px;text-align:center;'><div style='color:rgba(168,85,247,0.60);font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;'>💰 Prime Cost</div><div style='color:#c084fc;font-family:JetBrains Mono;font-size:1.15rem;font-weight:700;'>{format_inr(total_prime)}</div></div>",
                unsafe_allow_html=True
            )
        with budget_col2:
            st.markdown(
                f"<div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:16px 18px;text-align:center;'><div style='color:rgba(168,85,247,0.60);font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;'>🏦 Est. Budget <span style='color:#4ade80;font-size:9px;'>({budget_source})</span></div><div style='color:#e2e8f0;font-family:JetBrains Mono;font-size:1.15rem;font-weight:700;'>{format_inr(estimated_budget)}</div></div>",
                unsafe_allow_html=True
            )

        st.markdown('<p class="label-text">Pricing Strategy</p>', unsafe_allow_html=True)
        c_s1, c_s2 = st.columns(2)
        overhead_pct = c_s1.slider("Overhead Recovery (%)", 0, 30, 12)
        profit_pct = c_s2.select_slider("Target Profit (%)", options=[5, 10, 15, 20, 25, 30], value=15)
        
        competitor_density = st.slider("Competitor Density (No. of bidders)", 1, 12, 6)

    with right_col:
        # DYNAMIC BID: Use user's selected values from sliders
        live_bid = total_prime * (1 + overhead_pct / 100) * (1 + profit_pct / 100)
        live_gross_profit = live_bid - total_prime

        # Use the pure function (no side effects) for the live display
        live_win_prob = _predict_pure(
            prime_cost=total_prime,
            overhead_pct=overhead_pct,
            profit_pct=profit_pct,
            estimated_budget=estimated_budget,
            complexity_score=st.session_state.complexity_score,
            competitors=competitor_density,
            boq_context=boq_context,
        )

        # AI OPTIMIZATION: sweep profit %, using pure function to avoid session state pollution
        base_for_ai = total_prime * (1 + overhead_pct / 100)
        best_score = -1
        ai_recommended_profit = profit_pct
        ai_recommended_bid = live_bid
        ai_recommended_win_prob = live_win_prob

        for p in range(5, 31):
            bid_candidate = base_for_ai * (1 + p / 100)
            wp = _predict_pure(
                prime_cost=total_prime,
                overhead_pct=overhead_pct,
                profit_pct=p,
                estimated_budget=estimated_budget,
                complexity_score=st.session_state.complexity_score,
                competitors=competitor_density,
                boq_context=boq_context,
            )
            # Score: balance win chance (70%) with profit level (30%)
            score = (wp * 0.70) + ((p / 30) * 0.30)
            if score > best_score:
                best_score = score
                ai_recommended_profit = p
                ai_recommended_bid = bid_candidate
                ai_recommended_win_prob = wp

        # DISPLAY: Show bid based on USER'S slider selections (dynamic)
        st.markdown(f"""
            <div class="bid-box">
                <div style="position:relative;z-index:1;color:#DDD6FE;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:2px;">Final Optimized Bid</div>
                <div class="bid-price">{format_inr(live_bid)}</div>
                <div style="font-size:0.82rem;color:#C4B5FD;opacity:0.85;position:relative;z-index:1;">
                    Gross Profit: {format_inr(live_gross_profit)}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        st.markdown('<p class="label-text">AI Win Confidence</p>', unsafe_allow_html=True)
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=live_win_prob * 100,
            number={'suffix': "%", 'font': {'size': 36, 'color': '#e9d5ff', 'family': 'JetBrains Mono'}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': 'rgba(255,255,255,0.15)', 'tickwidth': 1},
                'bar': {'color': '#a855f7', 'thickness': 0.25},
                'bgcolor': 'rgba(255,255,255,0.03)',
                'borderwidth': 1,
                'bordercolor': 'rgba(255,255,255,0.08)',
                'steps': [
                    {'range': [0, 30], 'color': 'rgba(248,113,113,0.08)'},
                    {'range': [30, 60], 'color': 'rgba(251,191,36,0.06)'},
                    {'range': [60, 100], 'color': 'rgba(74,222,128,0.06)'},
                ],
                'threshold': {
                    'line': {'color': '#c084fc', 'width': 2},
                    'thickness': 0.8,
                    'value': live_win_prob * 100
                }
            }
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': 'rgba(255,255,255,0.7)', 'family': 'Inter'},
            height=220,
            margin=dict(l=30, r=30, t=30, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Dynamic Feedback based on USER'S current selection
        if live_win_prob >= 0.75:
            st.success("✅ **Strong Positioning** — Your bid is competitively priced.")
        elif live_win_prob >= 0.50:
            st.warning("⚖️ **Competitive Baseline** — Within winning range, tighten margins to improve.")
        elif live_win_prob >= 0.30:
            st.error("⚠️ **Moderate Risk** — Consider reducing profit or overhead percentage.")
        else:
            st.error("🚨 **Low Win Probability** — Bid is likely over budget or too aggressive.")

        # Contextual metrics panel
        price_ratio_display = live_bid / max(estimated_budget, 1)
        st.markdown(f"""
        <div class="tf-metric-grid">
            <div class="tf-metric-label">Win Probability</div>
            <div class="tf-metric-value" style="color:#a855f7">{live_win_prob*100:.1f}%</div>
            <div class="tf-metric-label">Your Profit Margin</div>
            <div class="tf-metric-value">{profit_pct}%</div>
            <div class="tf-metric-label">Bid / Budget Ratio</div>
            <div class="tf-metric-value" style="color:{'#4ade80' if price_ratio_display <= 1 else '#f87171'}">{price_ratio_display:.2f}×</div>
            <div class="tf-metric-label">Complexity Score</div>
            <div class="tf-metric-value">{complexity_score}/10</div>
            <div class="tf-metric-highlight">🤖 AI Recommended Profit: {ai_recommended_profit}% — Est. Win {ai_recommended_win_prob*100:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

        # AI Suggestion comparing user's choice vs AI recommendation
        if ai_recommended_profit != profit_pct:
            profit_diff = ai_recommended_profit - profit_pct
            win_diff = (ai_recommended_win_prob - live_win_prob) * 100
            direction = "Reducing" if profit_diff < 0 else "Increasing"
            effect = "increase" if win_diff > 0 else "shift"
            st.info(f"💡 **AI Suggestion:** {direction} profit to {ai_recommended_profit}% could {effect} win chance by ~{abs(win_diff):.1f}% (AI Recommended Bid: {format_inr(ai_recommended_bid)}).")
        else:
            st.success("✅ **Your selection matches AI recommendation!**")


        
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<p class="label-text">💾 Save Strategy</p>', unsafe_allow_html=True)

        # ✅ Inputs side-by-side
        f1, f2 = st.columns(2, gap="medium")

        with f1:
            st.markdown(
                '<span style="color:rgba(168,85,247,0.70);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;">Project Name <span style="color:#ef4444;">*</span></span>',
                unsafe_allow_html=True
            )
            project_name_input = st.text_input(
                "Project Name",
                value="",
                placeholder="Enter project name (required)...",
                help="Name for this bid strategy (mandatory)",
                key="bid_project_name",
                label_visibility="collapsed"
            )

        with f2:
            st.markdown(
                '<span style="color:rgba(168,85,247,0.70);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;">Category <span style="color:#ef4444;">*</span></span>',
                unsafe_allow_html=True
            )
            category_options = [
                "Select any one",
                "Infrastructure",
                "IT & Technology",
                "Construction",
                "Supply & Procurement",
                "Consulting Services",
                "Maintenance & Operations",
                "Healthcare",
                "Education",
                "Energy & Utilities",
                "Transport & Logistics",
                "Other"
            ]
            project_category = st.selectbox(
                "Category",
                options=category_options,
                index=0,
                help="Select the category for this bid (mandatory)",
                key="bid_category",
                label_visibility="collapsed"
            )

        # ✅ Buttons side-by-side equally (inside btn1)
        b1, b2 = st.columns(2, gap="medium")

        with b1:
            save_clicked = st.button("💾 Save Strategy", use_container_width=True)

        with b2:
            push_clicked = st.button("🚀 Push Proposal", type="primary", use_container_width=True)

        # ✅ Same save logic (just triggered from save_clicked)
        if save_clicked and not st.session_state.strategy_saved:
            if not project_name_input or not project_name_input.strip():
                st.warning("⚠️ Please enter a project name before saving.")
            elif project_category == "Select any one":
                st.warning("⚠️ Please select a category before saving.")
            else:
                try:
                    company_id = st.session_state["active_company_id"]
                    user_id = st.session_state.get("user_id")

                    res = supabase.table("bid_history_v2").insert({
                        "company_id": company_id,
                        "tender_id": st.session_state.tender_id,
                        "project_name": project_name_input.strip(),
                        "category": project_category,
                        "prime_cost": total_prime / 100000,
                        "overhead_pct": overhead_pct,
                        "profit_pct": profit_pct,
                        "competitor_density": competitor_density,
                        "complexity_score": st.session_state.complexity_score,
                        "final_bid_amount": live_bid / 100000,
                        "win_probability": live_win_prob,
                        "won": None
                    }).execute()

                    if res.data:
                        st.session_state.strategy_saved = True
                        st.toast(f"✅ Strategy saved for '{project_name_input}'")
                    else:
                        st.error("❌ Insert returned no data")

                except Exception as e:
                    st.error(f"Save failed: {e}")

        # Same push logic
        if push_clicked:
            st.balloons()

    # ═══════════════════════════════════════════════════════════════
    # PAST PROPOSAL ANALYZER  —  Navigate to dedicated page
    # ═══════════════════════════════════════════════════════════════
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    <div style="
        margin:20px 0 18px;padding:24px 28px;
        background:linear-gradient(135deg, rgba(124,58,237,0.10) 0%, rgba(15,17,26,0.85) 40%, rgba(168,85,247,0.06) 100%);
        border:1px solid rgba(168,85,247,0.18);border-radius:24px;
        position:relative;overflow:hidden;
    ">
        <div style="position:absolute;top:-40%;right:-10%;width:300px;height:300px;
             background:radial-gradient(circle,rgba(168,85,247,0.12) 0%,transparent 70%);pointer-events:none;"></div>
        <div style="display:flex;justify-content:space-between;align-items:center;position:relative;z-index:1;flex-wrap:wrap;gap:16px;">
            <div>
                <div style="font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:2.5px;color:rgba(168,85,247,0.65);margin-bottom:6px;">AI-Powered Module</div>
                <h2 style="margin:0;font-size:1.5rem;font-weight:900;background:linear-gradient(135deg,#fff 0%,#e9d5ff 50%,#c084fc 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Past Proposal Analyzer</h2>
                <p style="color:rgba(255,255,255,0.40);font-size:12px;margin:4px 0 0;">Analyze past tenders to discover winning patterns, average bids &amp; competitive intelligence — now on its own dedicated page.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Navigate to dedicated Past Proposal Analyzer page ──
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    _, btn_center, _ = st.columns([1, 1, 1])
    with btn_center:
        if st.button("📊 Open Past Proposal Analyzer →", use_container_width=True, key="btn_goto_ppa"):
            st.switch_page("pages/pastProposalAnalyzer.py")

bid_generation_page()

