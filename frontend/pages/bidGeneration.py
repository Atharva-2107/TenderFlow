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
        timeout=30
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

# def auto_fill_rates(boq_items, tender_text):
#     if not os.getenv("GROQ_API_KEY"):
#         return boq_items

#     priced_items = []

#     for item in boq_items:
#         task = item["Task"]
#         rate = 0

#         for attempt in range(2):  # 🔁 retry once
#             prompt = f"""
# You are an Indian tender costing expert.

# Decide whether the item is MATERIAL or SERVICE and assign a realistic Indian market rate.

# Rules:
# - Assume quantity = 1
# - Rate must be a NUMBER greater than 0
# - NO explanation
# - NO ranges
# - Output STRICT JSON ONLY

# FORMAT:
# {{ "rate": 7500 }}

# Item:
# "{task}"

# Tender context:
# {tender_text[:2000]}
# """

#             try:
#                 response = requests.post(
#                     "https://api.groq.com/openai/v1/chat/completions",
#                     headers={
#                         "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
#                         "Content-Type": "application/json"
#                     },
#                     json={
#                         "model": "llama-3.1-8b-instant",
#                         "messages": [{"role": "user", "content": prompt}],
#                         "temperature": 0.1
#                     },
#                     timeout=20
#                 )

#                 data = response.json()
#                 raw = data["choices"][0]["message"]["content"]

#                 parsed = safe_json_parse(raw)
#                 if isinstance(parsed, dict) and "rate" in parsed:
#                     rate = int(parsed["rate"])
#                     if rate > 0:
#                         break  # ✅ success

#             except Exception as e:
#                 pass

#         if rate == 0:
#             st.warning(f"⚠️ AI could not price: {task}")

#         priced_items.append({
#             "Task": task,
#             "Qty": 1,
#             "Rate": rate
#         })

#     return priced_items

def auto_fill_rates(boq_items, tender_text):
    if not os.getenv("GROQ_API_KEY"):
        return boq_items

    priced_items = []

    for item in boq_items:
        task = item["Task"]

        prompt = f"""
You are an Indian tender costing expert.

Your job:
- Decide whether the item is a MATERIAL or a SERVICE
- Estimate a realistic Indian market rate in INR

Pricing rules:
- If MATERIAL:
  • Use Indian market supply rate
  • Example: cement, steel, cables, pipes, equipment
- If SERVICE / CHARGE:
  • Use professional, logistics, statutory, or compensation rates
- Assume unit quantity = 1
- Rate must NOT be zero
- No flat pricing across items
- No explanations

Return ONLY a single number (INR).

Tender item:
"{task}"

Tender context:
{tender_text[:2000]}
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
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.25
                },
                timeout=20
            )

            data = response.json()
            raw = data["choices"][0]["message"]["content"].strip()

            match = re.search(r"\d[\d,]*", raw)
            rate = int(match.group().replace(",", "")) if match else 0

        except Exception:
            rate = 0

        priced_items.append({
            "Task": task,
            "Qty": 1,
            "Rate": rate
        })

    return priced_items

# also originally defined here

# def auto_fill_rates(boq_items, tender_text):
#     if not os.getenv("GROQ_API_KEY"):
#         return boq_items

#     enriched_items = []
#     billable_items = []

#     for item in boq_items:
#         item_type = classify_item(item["Task"])  # ✅ DEFINE IT HERE

#         # 🚫 Skip non-billable items completely
#         if item_type == "non_billable":
#             item["Qty"] = 0
#             item["Rate"] = 0
#             continue

#         # 🧱 Material fallback pricing
#         if item["Rate"] == 0 and item_type == "material":
#             t = item["Task"].lower()
#             for k, v in DEFAULT_MATERIAL_RATES.items():
#                 if k in t:
#                     item["Rate"] = v
#                     item["Qty"] = 1
#                     break

#         # 📦 Collect for AI pricing
#         enriched_items.append({
#             "task": item["Task"],
#             "type": item_type
#         })

#         billable_items.append(item)

#     prompt = f"""
# You are an Indian tender costing expert.

# For each item below, estimate a REALISTIC Indian market rate in INR.

# Rules:
# - If type = "material":
#   - Use typical Indian market supply rates
#   - Assume unit quantity = 1
# - If type = "service":
#   - Use professional / expert / compensation rates
# - NO flat pricing
# - Each item MUST have a different rate
# - Use realistic Indian market variance
# - Round to nearest 500 or 1000
# - Do NOT explain anything

# Return STRICT JSON ONLY in this format:
# [
#   {{"task": "...", "rate": 25000}}
# ]

# Items:
# {json.dumps(enriched_items, indent=2)}

# Tender context:
# {tender_text[:3000]}
# """

#     try:
#         response = requests.post(
#             "https://api.groq.com/openai/v1/chat/completions",
#             headers={
#                 "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
#                 "Content-Type": "application/json"
#             },
#             json={
#                 "model": "llama-3.1-70b-versatile",
#                 "messages": [{"role": "user", "content": prompt}],
#                 "temperature": 0.15
#             },
#             timeout=30
#         )

#         data = response.json()
#         if "choices" not in data:
#             return boq_items

#         raw = data["choices"][0]["message"]["content"]
#         parsed = safe_json_parse(raw)

#         rate_map = {}
#         for r in parsed:
#             if "task" in r and "rate" in r:
#                 key = re.sub(r"[^a-z0-9 ]", "", r["task"].lower())
#                 rate_map[key] = float(r["rate"])
                
#         # 🔥 APPLY AI RATES SAFELY
#         for item in boq_items:
#             clean_task = re.sub(r"[^a-z0-9 ]", "", item["Task"].lower())

#             if clean_task in rate_map:
#                 item["Rate"] = rate_map[clean_task]
#                 item["Qty"] = 1
    
#         # Apply rates
#         for item in boq_items:
#             clean_task = re.sub(r"[^a-z0-9 ]", "", item["Task"].lower())
#             item["Qty"] = 1
#             item["Rate"] = rate_map.get(clean_task, item.get("Rate", 0))

#         return boq_items

#     except Exception as e:
#         st.warning(f"AI pricing failed: {e}")
#         return boq_items

    
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
    # --- MODERN STYLING (Original CSS) ---
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
        .stApp { background-color: #09090B; color: #FAFAFA; font-family: 'Inter', sans-serif; }
        .glass-card {
            background: rgba(24, 24, 27, 0.8);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(63, 63, 70, 0.5);
            margin-bottom: 20px;
        }
        .bid-box {
            background: linear-gradient(135deg, #6D28D9 0%, #4C1D95 100%);
            border-radius: 16px;
            padding: 32px;
            text-align: center;
            box-shadow: 0 0 30px rgba(139, 92, 246, 0.2);
            border: 1px solid rgba(167, 139, 250, 0.3);
        }
        .bid-price {
            font-family: 'JetBrains Mono', monospace;
            font-size: 3.2rem;
            font-weight: 700;
            color: #FFFFFF;
            letter-spacing: -2px;
        }
        .label-text { color: #A1A1AA; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; }
        .stButton>button { border-radius: 10px; background-color: #7C3AED; color: white; border: none; font-weight: 600; width: 100%; }
        header, footer { visibility: hidden; }
        </style>
    """, unsafe_allow_html=True)

    # --- HEADER ---
    st.markdown("<h1 style='margin-bottom: 0;'>TenderFlow <span style='color: #A855F7;'>AI</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #71717A;'>Smart Bid Generation & Optimization Engine</p>", unsafe_allow_html=True)

    # --- INITIALIZATION LOGIC (CENTERED UI) ---
    if not st.session_state.extraction_done:
        st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
        _, col_mid, _ = st.columns([1, 2, 1]) 

        with col_mid:
            st.markdown('<div class="glass-card" style="text-align: center;">', unsafe_allow_html=True)
            st.markdown("### 📂 Initialize New Bid")
            st.write("Upload your technical proposal to begin AI cost extraction.")

            uploaded_tender = st.file_uploader(
                "Drop PDF here",
                type=["pdf"],
                label_visibility="collapsed"
            )

            if uploaded_tender:
                file_id = f"{uploaded_tender.name}_{uploaded_tender.size}"

                if st.session_state.get("processed_file") == file_id:
                    st.session_state.extraction_done = True
                else:
                    st.session_state.processed_file = file_id
                    
                if st.session_state.get("last_file") != uploaded_tender.name:
                    st.session_state.last_file = uploaded_tender.name
                    st.session_state.cost_df = pd.DataFrame(columns=["Task", "Qty", "Rate"])
                    st.session_state.extraction_done = False
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

                        st.write("🔍 Materials detected:", st.session_state.cost_df)
                        
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
                        supabase.table("tenders").insert({
                            "authority_name": uploaded_tender.name,
                            "estimated_budget": tender_data["estimated_budget"],
                            "complexity_score": int(complexity_score),
                        }).execute()

                        st.session_state.extraction_done = True
                        st.rerun()

                        st.success("Tender analyzed successfully")
                        
                    except Exception as e:
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

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="label-text">AI Win Confidence</p>', unsafe_allow_html=True)
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=live_win_prob * 100,
            number={'suffix': "%"},
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#A855F7"}}
        ))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"**Your Current Win Chance:** {live_win_prob*100:.2f}%")
        st.markdown(f"**Your Selected Profit:** {profit_pct}%")
        st.markdown(f"**AI Recommended Profit:** {ai_recommended_profit}%")
        
        st.markdown(f"<div style='text-align:center; font-weight:600; color:#A855F7;'>{live_win_prob*100:.2f}% Chance of Winning</div>", unsafe_allow_html=True) 
        st.markdown(f"**Current Bid:** {format_inr(live_bid)}")
        st.markdown(f"**Complexity Score:** {complexity_score}/10")
        
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

        if st.button("💾 Save Strategy") and not st.session_state.strategy_saved:
            try:
                # 1. Get User and Company Context
                user = st.session_state.get("user")
                user_id = user.id if user else None
                
                company_id = st.session_state.get("company_id")
                if not company_id and user_id:
                    # Fallback fetch
                    resp = supabase.table("profiles").select("company_id").eq("id", user_id).maybe_single().execute()
                    if resp.data:
                        company_id = resp.data.get("company_id")
                        st.session_state["company_id"] = company_id
                        
                # 2. Link to Generated Tender (Notification)
                project_name = "Untitled Bid"
                if st.session_state.tender_data and "project_name" in st.session_state.tender_data:
                    project_name = st.session_state.tender_data["project_name"]
                
                gen_id = None
                # Check if tender exists in generated_tenders
                existing_tender = supabase.table("generated_tenders").select("id").eq("project_name", project_name).execute()
                
                if existing_tender.data:
                    gen_id = existing_tender.data[0]['id']
                else:
                    # Create new entry for dashboard notification
                    gen_res = supabase.table("generated_tenders").insert({
                        "project_name": project_name,
                        "status": "Open",
                        "user_id": user_id,
                        # Fill required fields with placeholders for Bid Strategy
                        "content": "Bid Strategy Only"
                    }).execute()
                    if gen_res.data:
                        gen_id = gen_res.data[0]['id']

                # 3. Save Bid History
                res = supabase.table("bid_history").insert({
                    "company_id": company_id,
                    "tender_id": gen_id,
                    "prime_cost": total_prime / 100000,
                    "overhead_pct": overhead_pct,
                    "profit_pct": profit_pct,  # Save user's actual selection
                    "competitor_density": competitor_density,
                    "complexity_score": st.session_state.complexity_score, # Dynamic Score
                    "final_bid_amount": live_bid / 100000,  # Save user's actual bid
                    "win_probability": live_win_prob,  # Save user's actual win prob
                    "won": None # Will be updated via Dashboard
                }).execute()

                if res.data:
                    st.session_state.strategy_saved = True
                    st.toast("✅ Strategy saved successfully")
                else:
                    st.error("❌ Database insert failed")

            except Exception as e:
                st.error(f"Save failed: {e}")
        
        if st.button("🚀 Push Proposal", type="primary"):
            st.balloons()
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    bid_generation_page()