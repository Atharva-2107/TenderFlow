import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import json
import xgboost as xgb
import re
import os
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
    """Formats a number into Indian System (Lakhs/Crores)"""
    try:
        s, *d = str(f"{number:.2f}").partition(".")
        r = ",".join([s[x-2:x] for x in range(-3, -len(s), -2)][::-1] + [s[-3:]])
        return "₹" + "".join([r] + d)
    except:
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
    # st.code(raw, language="json")
    if not os.getenv("GROQ_API_KEY"):
        st.warning("Groq API key missing")
        return []

    prompt = f"""
    You are a tender BOQ extraction engine.

    From the tender document below, extract ALL billable or quote-required items.

    Include:
    - BOQ headings
    - Schedule items
    - Commercial bid items
    - Compensation / payment items
    - Charges, fees, services, deliverables

    Rules:
    - Headings only (NOT full sentences)
    - 3–12 words per item
    - No quantities
    - No rates
    - No explanations
    - Output ONLY a valid JSON array of strings
    - Max 30 items

    EXAMPLE OUTPUT:
    [
    "Hardship compensation amount",
    "Monthly displacement compensation",
    "Stamp duty and registration charges"
    ]

    TENDER TEXT:
    {text[:4000]}

    """

    try:
            response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0
        },
        timeout=15
            )

            data = response.json()

            # 🔍 FULL DEBUG (TEMPORARY)
            # st.write("🔴 Raw Groq response:")
            # st.json(data)

            if "choices" not in data:
                error_msg = data.get("error", {}).get("message", "Unknown Groq error")
                st.error(f"Groq error: {error_msg}")
                return []
            
            raw = data["choices"][0]["message"]["content"]

            # 🔍 DEBUG (temporary – REMOVE after verification)
            # st.code(raw, language="json")

            items = safe_json_parse(raw)

            return [
                {"Task": normalize_task(item), "Qty": 1, "Rate": 0}
                for item in items
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

        prompt = f"""
You are an Indian procurement & tender costing expert.

Determine a realistic **Indian local market rate** for the item below.

Rules:
- Decide whether the item is MATERIAL or SERVICE
- Assume quantity = 1
- Use Indian market norms (2024–2025)
- Rate MUST be a single number in INR
- NO ranges, NO explanation
- If unsure, give your best expert estimate

Return STRICT JSON only:

{{
  "rate": 12345
}}

Item:
"{task}"

Tender context (for scale only):
{tender_text[:1500]}
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
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2
                },
                timeout=15
            )

            data = response.json()
            raw = data["choices"][0]["message"]["content"]

            parsed = safe_json_parse(raw)
            if isinstance(parsed, dict) and "rate" in parsed:
                rate = int(parsed["rate"])

        except Exception as e:
            rate = 0

        priced_items.append({
            "Task": task,
            "Qty": 1,
            "Rate": rate
        })

    return priced_items


    
def predict_win_api(prime_cost_rs, overhead_pct, profit_pct, estimated_budget_rs, complexity, competitors):
    """Original API Logic with Fallback simulation"""
    payload = {
        "prime_cost_lakh": prime_cost_rs / 100000,
        "overhead_pct": overhead_pct,
        "profit_pct": profit_pct,
        "estimated_budget_lakh": estimated_budget_rs / 100000,
        "complexity_score": int(complexity),
        "competitor_density": int(competitors),
    }

    try:
        r = requests.post("http://127.0.0.1:8000/predict-win", json=payload, timeout=2)
        data = r.json()
        if "win_probability" in data: return data["win_probability"]
        elif "probability" in data: return data["probability"]
        elif "win_prob" in data: return data["win_prob"]
        return 0.5
    except:
        # Fallback Simulation Logic (Maintains responsiveness if API is down)
        base = 0.85
        prob = base - (profit_pct * 0.015) - (competitors * 0.04)
        return max(0.05, min(0.95, prob))

def bid_generation_page():
    if not st.session_state.get("authenticated"):
        st.error("Please login to continue.")
        st.stop()

    if not st.session_state.get("active_company_id"):
        st.error("Company context missing. Please login again.")
        st.stop()
    # --- MODERN STYLING (Original CSS) ---
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600;700&display=swap');

:root{
    --bg1: #1a1c4b;
    --bg2: #0f111a;
    --card: rgba(24, 24, 27, 0.82);
    --card2: rgba(18, 18, 22, 0.72);
    --border: rgba(255, 255, 255, 0.10);
    --border2: rgba(168, 85, 247, 0.22);
    --text: #F4F4F5;
    --muted: rgba(244, 244, 245, 0.65);
    --muted2: rgba(244, 244, 245, 0.45);
    --accent: #A855F7;
    --accent2: rgba(168, 85, 247, 0.18);
    --shadow: 0 18px 45px rgba(0,0,0,0.35);
    --shadowSoft: 0 10px 25px rgba(0,0,0,0.25);
    --radius: 18px;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    color: var(--text) !important;
}

/* Streamlit App Background */
.stApp {
    background: radial-gradient(circle at 20% 30%, var(--bg1) 0%, var(--bg2) 100%) !important;
}

/* Hide default Streamlit header/footer */
header { visibility: hidden; }
footer { visibility: hidden; }

/* Reduce top padding */
div.block-container {
    padding-top: 0.6rem !important;
    padding-bottom: 2.2rem !important;
}

/* ====== Global Typography ====== */
h1, h2, h3, h4 {
    letter-spacing: -0.02em !important;
    font-weight: 700 !important;
    color: var(--text) !important;
}

p, label, div {
    color: var(--text) !important;
}
small, .stCaption, .stMarkdown p {
    color: var(--muted) !important;
}

/* ====== Header Nav Container ====== */
.header-nav {
    background: linear-gradient(
        135deg,
        rgba(255,255,255,0.10),
        rgba(255,255,255,0.03)
    );
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 12px 18px;
    margin-bottom: 18px;
    box-shadow: var(--shadowSoft);
    backdrop-filter: blur(12px);
}

/* ====== Cards ====== */
.glass-card {
    background: transparent !important;
    border-radius: var(--radius);
    padding: 10px 10px;
    border: 1px solid var(--border);
    box-shadow: var(--shadowSoft);
    margin-bottom: 18px;
    position: relative;
    overflow: hidden;
}

.glass-card:before{
    content:"";
    position:absolute;
    inset:0;
    background: radial-gradient(circle at 20% 10%, var(--accent2) 0%, transparent 55%);
    pointer-events:none;
}

/* ====== Premium Bid Box ====== */
.bid-box {
    background: linear-gradient(135deg, rgba(168, 85, 247, 0.35) 0%, rgba(15, 17, 26, 0.9) 55%, rgba(168, 85, 247, 0.18) 100%);
    border-radius: 22px;
    padding: 28px 26px;
    text-align: center;
    box-shadow: 0 22px 55px rgba(168, 85, 247, 0.15);
    border: 1px solid rgba(168, 85, 247, 0.28);
    position: relative;
    overflow: hidden;
}

.bid-box:after{
    content:"";
    position:absolute;
    width: 420px;
    height: 420px;
    top: -250px;
    left: -250px;
    background: radial-gradient(circle, rgba(168, 85, 247, 0.35) 0%, transparent 60%);
    filter: blur(2px);
    pointer-events:none;
}

/* Big Price */
.bid-price {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 3.1rem;
    font-weight: 700;
    color: #FFFFFF !important;
    letter-spacing: -1.5px;
    margin-top: 6px;
    margin-bottom: 6px;
}

/* Labels */
.label-text {
    color: var(--muted2) !important;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.14em;
}

/* ====== Buttons (Global) ====== */
.stButton>button {
    width: 100%;
    border-radius: 14px !important;
    border: 1px solid rgba(168, 85, 247, 0.25) !important;
    background: linear-gradient(135deg, rgba(168, 85, 247, 0.95) 0%, rgba(124, 58, 237, 0.85) 100%) !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 0.7rem 1rem !important;
    box-shadow: 0 14px 35px rgba(168, 85, 247, 0.22) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease, border 0.15s ease;
}

.stButton>button:hover {
    transform: translateY(-1px);
    box-shadow: 0 18px 40px rgba(168, 85, 247, 0.28) !important;
    border: 1px solid rgba(168, 85, 247, 0.45) !important;
}

.stButton>button:active {
    transform: translateY(0px) scale(0.99);
}

/* Disabled buttons */
.stButton>button:disabled {
    opacity: 0.55 !important;
    cursor: not-allowed !important;
    box-shadow: none !important;
}

/* ====== Sliders / Inputs ====== */
.stSlider label, .stSelectSlider label {
    font-weight: 600 !important;
    color: var(--muted) !important;
}
                
div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"]{
    background-color: #FFFFFF !important;
    border: 2px solid #FFFFFF !important;
    box-shadow: 0 0 0 4px rgba(168, 85, 247, 0.20) !important; /* optional glow */
}

.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
}

.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border: 1px solid rgba(168, 85, 247, 0.55) !important;
    box-shadow: 0 0 0 4px rgba(168, 85, 247, 0.15) !important;
}

/* ====== Data Editor Styling ====== */
div[data-testid="stDataFrame"] {
    border-radius: var(--radius) !important;
    overflow: hidden !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: var(--shadowSoft);
}

div[data-testid="stDataFrame"] * {
    font-size: 0.92rem !important;
}

/* ====== Divider ====== */
hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, rgba(168,85,247,0.35), transparent) !important;
    margin: 10px 0 18px 0 !important;
}

/* Track fill (progress) */
div[data-testid="stSlider"] [data-baseweb="slider"] div > div > div{
    background-color: var(--accent) !important;
    border-radius: 10px 10px;
}


/* =========================
   FIX 1: Right panel alignment
   (Win chance / profit / bid / complexity)
   ========================= */
.tf-metric-grid{
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 10px 16px;
    margin-top: 8px;
    padding: 14px 14px;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.10);
    background: rgba(255,255,255,0.04);
}

.tf-metric-label{
    font-size: 0.92rem;
    font-weight: 600;
    color: var(--muted) !important;
}

.tf-metric-value{
    font-size: 2rem;
    font-weight: 700;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
    text-align: right;
}

.tf-metric-highlight{
    grid-column: 1 / -1;
    text-align: center;
    margin-top: 6px;
    padding-top: 10px;
    border-top: 1px solid rgba(168,85,247,0.22);
    font-size: 1rem;
    font-weight: 800;
    color: var(--accent) !important;
}
                
/* ====== Alerts look premium ====== */
.stAlert {
    border-radius: 14px !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    background: rgba(255,255,255,0.06) !important;
    box-shadow: var(--shadowSoft);
}

/* Make markdown links accent */
a {
    color: var(--accent) !important;
    text-decoration: none !important;
}
a:hover {
    text-decoration: underline !important;
}

/* ====== Scrollbar (subtle premium) ====== */
::-webkit-scrollbar {
    width: 10px;
}
::-webkit-scrollbar-track {
    background: rgba(255,255,255,0.04);
}
::-webkit-scrollbar-thumb {
    background: rgba(168, 85, 247, 0.35);
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(168, 85, 247, 0.55);
}
                
/* Fix: stop HTML being displayed like code/text */
.tf-metric-grid-wrap{
    all: unset;
    display: block;
}

.tf-metric-grid-wrap *{
    white-space: normal !important;
}


</style>
""", unsafe_allow_html=True)

    # st.markdown("""
    #     <style>
    #     @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
    #     .stApp { background: radial-gradient(circle at 20% 30%, #1a1c4b 0%, #0f111a 100%); color: #FAFAFA; font-family: 'Inter', sans-serif; }
                
    #     header { visibility: hidden; }

    #     div.block-container {
    #         padding-top: 0.3rem !important; 
    #     }
                
    #     /* HEADER NAV CONTAINER */
    #     .header-nav {
    #         background: linear-gradient(
    #             135deg,
    #             rgba(255,255,255,0.08),
    #             rgba(255,255,255,0.02)
    #         );
    #         backdrop-filter: blur(10px);
    #         border: 1px solid rgba(255,255,255,0.12);
    #         border-radius: 16px;
    #         padding: 12px 18px;
    #         margin-bottom: 22px;
    #     }

    #     .glass-card {
    #         background: rgba(24, 24, 27, 0.8);
    #         border-radius: 16px;
    #         padding: 24px;
    #         border: 1px solid rgba(63, 63, 70, 0.5);
    #         margin-bottom: 20px;
    #     }
    #     .bid-box {
    #         background: linear-gradient(135deg, #6D28D9 0%, #4C1D95 100%);
    #         border-radius: 16px;
    #         padding: 32px;
    #         text-align: center;
    #         box-shadow: 0 0 30px rgba(139, 92, 246, 0.2);
    #         border: 1px solid rgba(167, 139, 250, 0.3);
    #     }
    #     .bid-price {
    #         font-family: 'JetBrains Mono', monospace;
    #         font-size: 3.2rem;
    #         font-weight: 700;
    #         color: #FFFFFF;
    #         letter-spacing: -2px;
    #     }
    #     .label-text { color: #A1A1AA; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; }
    #     .stButton>button { border-radius: 10px; background-color: #7C3AED; color: white; border: none; font-weight: 600; width: 100%; }
    #     header, footer { visibility: hidden; }
    #     </style>
    # """, unsafe_allow_html=True)

    # HEADER NAVIGATION
    left, center = st.columns([3, 6])

    with left:
        logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
        logo = get_base64_of_bin_file(logo_path)

        if logo:
            st.markdown(f"""
                <div style="display:flex; align-items:center;">
                    <img src="data:image/png;base64,{logo}" width="200">
                </div>
            """, unsafe_allow_html=True)

    with center:
        header_cols = st.columns([3, 0.4, 0.4, 0.4, 0.4, 0.4])

        with header_cols[1]:
            if st.button("⊞", key="h_dash", help="Dashboard"):
                st.switch_page("app.py")

        with header_cols[2]:
            if can_access("tender_generation"):
                if st.button("⎘", key="h_gen", help="Tender Generation"):
                    st.switch_page("pages/tenderGeneration.py")
            else:
                st.button("⎘", key="h_gen_disabled", disabled=True, help="Access restricted")


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

    st.markdown("<div> <hr> </div>", unsafe_allow_html=True)
    # --- HEADER ---
    st.markdown("<h1 style='margin-bottom: 0;'>Bid <span style='color: #a855f7;'>Generation</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #71717A;'>Smart Bid Generation & Optimization Engine</p>", unsafe_allow_html=True)

    # --- INITIALIZATION LOGIC (CENTERED UI) ---
    if not st.session_state.extraction_done:
        st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
        _, col_mid, _ = st.columns([1, 2, 1]) 

        with col_mid:
            # st.markdown('<div class="glass-card" style="text-align: center;">', unsafe_allow_html=True)
            st.markdown("### 📂 Initialize New Bid")
            st.write("Upload your technical proposal to begin AI cost extraction.")

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
                    
                # Reset state for new file
                if st.session_state.get("last_file") != uploaded_tender.name:
                    st.session_state.last_file = uploaded_tender.name
                    st.session_state.cost_df = pd.DataFrame(columns=["Task", "Qty", "Rate"])
                    st.session_state.extraction_done = False
                    st.session_state.processed_file = None
                
                # Mark as analyzing to prevent duplicate runs
                st.session_state.analyzing_file = file_id
                
                with st.spinner("🔮 Analyzing tender…"):
                    try:
                        reader = PdfReader(uploaded_tender)
                        text = " ".join([p.extract_text() or "" for p in reader.pages])
                        
                        def extract_boq_items(text):
                            MATERIAL_MAP = {
                                "excavation": "Excavation",
                                "earthwork": "Earthwork",
                                "pcc": "PCC Concrete",
                                "plain cement concrete": "PCC Concrete",
                                "rcc": "RCC Concrete",
                                "reinforcement": "Steel Reinforcement",
                                "steel": "Steel Reinforcement",
                                "brick": "Brick Masonry",
                                "plaster": "Plastering",
                                "formwork": "Formwork",
                                "foundation": "Foundation Work",
                                "column": "RCC Columns",
                                "beam": "RCC Beams",
                                "slab": "RCC Slab",
                                "pile": "Pile Foundation"
                            }

                            found_materials = set()
                            text_lower = text.lower()

                            for key, material in MATERIAL_MAP.items():
                                if key in text_lower:
                                    found_materials.add(material)

                            return [
                                {"Task": m, "Qty": 0, "Rate": 0}
                                for m in sorted(found_materials)
                            ]

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
                            # Search for the label followed by currency and digits/commas
                            m = re.search(rf"{label}.*?₹\s?([\d,]+)", text, re.IGNORECASE)
                            
                            # Check if a match was found AND if group 1 actually contains text
                            if m and m.group(1):
                                clean_str = m.group(1).replace(",", "")
                                try:
                                    return float(clean_str)
                                except ValueError:
                                    return 0.0
                            return 0.0  # Return 0.0 instead of None to prevent downstream math error

                        tender_data = {
                            "estimated_budget": extract_amount("Estimated Cost|Tender Value"),
                            "emd": extract_amount("EMD"),
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

    # --- DASHBOARD VIEW (AFTER EXTRACTION) ---
    tender_data = st.session_state.tender_data or {}
    complexity_score = st.session_state.complexity_score or 5

    st.divider()
    left_col, right_col = st.columns([1.8, 1.2], gap="large")
    st.caption("🤖 Materials suggested by AI. Please verify quantities & rates before bidding.")
    with left_col:
        st.markdown('<p class="label-text">Resource Ledger</p>', unsafe_allow_html=True)
        
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
        
        total_prime = (edited_df['Qty'] * edited_df['Rate']).sum()
        # edited_df["Qty"] = pd.to_numeric(edited_df["Qty"], errors="coerce").fillna(0)
        # edited_df["Rate"] = pd.to_numeric(edited_df["Rate"], errors="coerce").fillna(0)

        st.session_state.cost_df = edited_df
        # Original Multiplier Logic
        multiplier = st.slider("Estimated Client Budget Multiplier", 1.05, 1.8, 1.3, 0.05)
        
        estimated_budget = (
            tender_data.get("estimated_budget")
            if tender_data.get("estimated_budget") is not None
            else total_prime * multiplier
        )
        
        st.markdown(f"<div style='text-align:right;color:#A1A1AA;'>Estimated Budget: {format_inr(estimated_budget)}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: right; color: #A855F7; font-family: JetBrains Mono; font-size: 1.2rem;'>Prime Cost: {format_inr(total_prime)}</div>", unsafe_allow_html=True)

        st.markdown('<p class="label-text">Pricing Strategy</p>', unsafe_allow_html=True)
        c_s1, c_s2 = st.columns(2)
        overhead_pct = c_s1.slider("Overhead Recovery (%)", 0, 30, 12)
        profit_pct = c_s2.select_slider("Target Profit (%)", options=[5, 10, 15, 20, 25, 30], value=15)
        
        competitor_density = st.slider("Competitor Density (No. of bidders)", 1, 12, 6)

    with right_col:
        # DYNAMIC BID: Use user's selected values from sliders
        live_bid = total_prime * (1 + overhead_pct/100) * (1 + profit_pct/100)
        live_gross_profit = live_bid - total_prime

        live_win_prob = predict_win_api(
            total_prime,
            overhead_pct,
            profit_pct,
            estimated_budget,
            st.session_state.complexity_score,
            competitor_density
        )

        # AI OPTIMIZATION: Find best profit % for recommendation (separate from user's choice)
        base = total_prime * (1 + overhead_pct / 100)
        best_score = -1
        ai_recommended_profit = profit_pct
        ai_recommended_bid = live_bid
        ai_recommended_win_prob = live_win_prob

        for p in range(5, 31):
            bid = base * (1 + p / 100)
            win_prob = predict_win_api(
                total_prime, overhead_pct, p,
                estimated_budget,
                st.session_state.complexity_score,
                competitor_density
            )
            score = (win_prob * 0.7) + ((p / 30) * 0.3)
            if score > best_score:
                best_score = score
                ai_recommended_profit = p
                ai_recommended_bid = bid
                ai_recommended_win_prob = win_prob

        # DISPLAY: Show bid based on USER'S slider selections (dynamic)
        st.markdown(f"""
            <div class="bid-box">
                <div class="label-text" style="color: #DDD6FE;">Final Optimized Bid</div>
                <div class="bid-price">{format_inr(live_bid)}</div>
                <div style="font-size: 0.85rem; color: #C4B5FD; opacity: 0.9;">
                    Gross Profit: {format_inr(live_gross_profit)}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<p class="label-text">AI Win Confidence</p>', unsafe_allow_html=True)
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=live_win_prob * 100,
            number={'suffix': "%"},
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#A855F7"}}
        ))
        st.plotly_chart(fig, use_container_width=True)

        # st.markdown(f"**Your Current Win Chance:** {live_win_prob*100:.2f}%")
        # st.markdown(f"**Your Selected Profit:** {profit_pct}%")
        # st.markdown(f"**AI Recommended Profit:** {ai_recommended_profit}%")
        
        # st.markdown(f"<div style='text-align:center; font-weight:600; color:#A855F7;'>{live_win_prob*100:.2f}% Chance of Winning</div>", unsafe_allow_html=True) 
        # st.markdown(f"**Current Bid:** {format_inr(live_bid)}")
        # st.markdown(f"**Complexity Score:** {complexity_score}/10")
        
        # Dynamic Feedback based on USER'S current selection
        if live_win_prob > 0.8:
            st.success("✅ **Strong Positioning**")
        elif live_win_prob > 0.5:
            st.warning("⚖️ **Competitive Baseline**")
        else:
            st.error("🚨 **Low Probability**")
        
        # AI Suggestion comparing user's choice vs AI recommendation
        if ai_recommended_profit != profit_pct:
            profit_diff = ai_recommended_profit - profit_pct
            win_diff = (ai_recommended_win_prob - live_win_prob) * 100
            if profit_diff < 0:
                st.info(f"💡 **AI Suggestion:** Reducing profit to {ai_recommended_profit}% could increase win chance by ~{win_diff:.1f}%.")
            else:
                st.info(f"💡 **AI Suggestion:** Consider {ai_recommended_profit}% profit margin for optimal balance.")
        else:
            st.success("✅ **Your selection matches AI recommendation!**")


        btn1, btn2 = st.columns([2,2])

    with btn1:
        # Project name input for saving (mandatory)
        st.markdown('<p class="label-text">Save Strategy</p>', unsafe_allow_html=True)
        st.markdown('<span style="color: #A855F7; font-size: 0.85rem;">Project Name <span style="color: #EF4444;">*</span></span>', unsafe_allow_html=True)
        project_name_input = st.text_input(
            "Project Name", 
            value="", 
            placeholder="Enter project name (required)...",
            help="Name for this bid strategy (mandatory)",
            key="bid_project_name",
            label_visibility="collapsed"
        )
        
        # Category dropdown (mandatory)
        st.markdown('<span style="color: #A855F7; font-size: 0.85rem;">Category <span style="color: #EF4444;">*</span></span>', unsafe_allow_html=True)
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
        
        if st.button("💾 Save Strategy", use_container_width=True) and not st.session_state.strategy_saved:
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

    with btn2:
        if st.button("🚀 Push Proposal", type="primary"):
            st.balloons()

        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    bid_generation_page()