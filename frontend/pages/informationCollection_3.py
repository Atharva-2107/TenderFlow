import streamlit as st
import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
import re
import time
from datetime import date

# PAGE CONFIG
st.set_page_config(page_title="TenderFlow | Financial Capacity", layout="wide")

if not st.session_state.get("authenticated"):
    st.switch_page("pages/loginPage.py")
    st.stop()

if st.session_state.get("onboarding_complete"):
    st.switch_page("pages/dashboard.py")
    st.stop()
    
load_dotenv() 
   
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase environment variables not loaded")
    st.stop()

sb_session = st.session_state.get("sb_session")
user = st.session_state.get("user")

if not sb_session or not user:
    st.switch_page("pages/loginPage.py")
    st.stop()

user_id = user.id
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Session Refresh Logic
try:
    refreshed = supabase.auth.refresh_session(sb_session.refresh_token)
    st.session_state["sb_session"] = refreshed.session
    sb_session = refreshed.session
    if sb_session is None:
        st.error("Session expired. Please log in again.")
        st.switch_page("pages/loginPage.py")
        st.stop()
except Exception:
    st.error("Session expired. Please log in again.")
    st.switch_page("pages/loginPage.py")
    st.stop()
    
supabase.postgrest.auth(sb_session.access_token)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

def upload_file(file, filename):
    if not file:
        return None
    
    if file.size > MAX_FILE_SIZE:
        st.error(f"{file.name} exceeds 5MB size limit.")
        st.stop()

    path = f"{user_id}/{filename}"

    try:
        supabase.storage.from_("compliance_docs").upload(
            path,
            file.getvalue(),
            {"content-type": file.type, "upsert": "true"}
        )
        return path
    except Exception:
        # If file exists, return existing path
        return path

# UTILS
def get_base64_of_bin_file(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        return None
    return None

# STYLING
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    button[title="View header anchor"], .stHtmlHeader a, [data-testid="stHeaderActionElements"] {
        display: none !important;
    }
    header { visibility: hidden !important; }
            
    .stApp {
        background-color: #0f111a;
        font-family: 'Inter', sans-serif;
    }

    .block-container {
        padding-top: 2rem !important;
        max-width: 1100px !important;
        margin: auto;
    }
    
    .centered-header {
            text-align: center;
            width: 100%;
            margin-top: 20px;
            margin-bottom: 20px;
    }

    h1 {
        color: white !important;
        font-weight: 800 !important;
        letter-spacing: -1px;
        font-size: 40px !important;
        margin-bottom: 5px !important;
    }
    
    .sub-text {
        color: #94a3b8;
        font-size: 16px;
        margin-bottom: 3rem;
    }

    label {
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        color: #a855f7 !important; 
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stTextInput input, .stFileUploader section, .stTextArea textarea {
        background-color: #161925 !important;
        color: #FFFFFF !important;
        border: 1px solid #2d313e !important;
        border-radius: 8px !important;
    }

    div.stButton {
        display: flex;
        justify-content: center;
    }

    div.stButton > button {
        background-color: #7c3aed !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        padding: 10px 40px !important;
        font-weight: 600 !important;
        border: 1.5px solid #8b5cf6 !important;
        margin-top: 20px;
    }

    div.stButton > button:hover {
        background-color: #6d28d9 !important;
        border-color: #7c3aed !important;
    }

    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# LOGO
current_file_path = Path(__file__).resolve()
possible_paths = [
    current_file_path.parent / "assets" / "logo.png",
    current_file_path.parent.parent / "assets" / "logo.png"
]
logo_base64 = None
for p in possible_paths:
    if p.exists():
        logo_base64 = get_base64_of_bin_file(p)
        break

if logo_base64:
    st.markdown(f"""
        <div style="position: absolute; left: -250px; top: -20px;">
            <img src="data:image/png;base64,{logo_base64}" width="190">
        </div>
    """, unsafe_allow_html=True)

# CONTENT 
st.markdown("""
        <div class="centered-header">
            <h1>Financial Capacity</h1>
            <p class='sub-text'>Please provide turnover details and supporting audit documents.</p>
        </div>
        """, unsafe_allow_html=True)

c1, c2 = st.columns(2, gap='large')

with c1:
    st.markdown("<div style='margin-top: 17px;'></div>",unsafe_allow_html=True)
    avg_turnover = st.text_input("Average Annual Turnover (Last 3 FY)", placeholder="Enter amount in Lakhs/Crores")
    
    fy_wise = st.text_area("FY Wise Turnover Details", placeholder="e.g. FY23: 50L, FY22: 45L...", height=155)

with c2:
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    balance_sheet = st.file_uploader("Upload Audited Balance Sheet", type=['pdf'])
    
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    ca_cert = st.file_uploader("Upload CA Certificate", type=['pdf'])

# NAVIGATION
st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
b_col1, b_col2, b_col3 = st.columns([1, 1, 1])

with b_col1:
    if st.button(" <- Back "):
        st.switch_page("pages/informationCollection_2.py")

with b_col3:
    if st.button(" Next -> "):
        # Validations
        if not avg_turnover.strip():
            st.error("Average Annual Turnover is required.")
            st.stop()
        if not re.search(r"\d", avg_turnover):
            st.error("Turnover must contain numeric value.")
            st.stop()
        if not fy_wise.strip():
            st.error("FY-wise turnover details are required.")
            st.stop()
        if len(fy_wise.splitlines()) < 2:
            st.error("Provide turnover for at least 2 financial years.")
            st.stop()
        if not balance_sheet:
            st.error("Audited Balance Sheet is mandatory.")
            st.stop()
        if not ca_cert:
            st.error("CA Certificate is mandatory.")
            st.stop()

        # 1. GET COMPANY ID
        company_id = st.session_state.get("company_id")
        if not company_id:
            prof_check = supabase.table("profiles").select("company_id").eq("id", user_id).maybe_single().execute()
            company_id = prof_check.data.get("company_id") if prof_check.data else None
            st.session_state["company_id"] = company_id

        # 2. UPLOAD FILES
        with st.spinner("Uploading financial documents..."):
            balance_sheet_path = upload_file(balance_sheet, f"balance_sheet_{user_id}.pdf")
            ca_cert_path = upload_file(ca_cert, f"ca_certificate_{user_id}.pdf")

        # 3. PREPARE PAYLOAD
        financial_data = {
            "user_id": user_id,   
            "company_id": company_id, # LINKING DATA TO COMPANY
            "avg_annual_turnover": avg_turnover,
            "fy_wise_turnover": fy_wise,
            "balance_sheet_url": balance_sheet_path,
            "ca_certificate_url": ca_cert_path,
        }

        try:
            # 4. SAVE TO DATABASE
            supabase.table("financials").upsert(financial_data, on_conflict="user_id").execute()

            # 5. ADVANCE STEPS
            supabase.table("profiles").update({"onboarding_step": 4}).eq("id", user_id).execute()
            supabase.table("company_information").update({"onboarding_step": 4}).eq("id", user_id).execute()
            
            st.session_state["onboarding_step"] = 4

            # 6. REDIRECT
            st.switch_page("pages/informationCollection_4.py")
            st.stop()

        except Exception as e:
            st.error(f"Error saving financial data: {e}")