import streamlit as st
import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
import re
import time

# PAGE CONFIG
st.set_page_config(page_title="TenderFlow | Compliance", layout="wide")

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

MAX_FILE_SIZE = 5 * 1024 * 1024  # (5MB MAX)

def upload_file(file, filename):
    if not file:
        return None
    
    if file.size > MAX_FILE_SIZE:
        st.error(f"{file.name} exceeds Max size i.e 5MB")
        st.stop()

    path = f"{user_id}/{filename}"

    try:
        supabase.storage.from_("compliance_docs").upload(
            path,
            file.getvalue(),
            {"content-type": file.type, "upsert": "true"}
        )
        return path
    except Exception as e:
        # If file already exists, we return the path anyway
        return path

# UTILS: 
def get_base64_of_bin_file(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        return None
    return None

GST_REGEX = r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}$"
PAN_REGEX = r"^[A-Z]{5}\d{4}[A-Z]$"
IFSC_REGEX = r"^[A-Z]{4}0[A-Z0-9]{6}$"

def is_valid(regex, value):
    return re.match(regex, value)

# PREMIUM DARK CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    [data-testid="stHeaderActionElements"], .st-emotion-cache-16idsys p a, button[title="View header anchor"] {
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

    .stTextInput input, .stFileUploader section {
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
            <h1>Legal & Tax Compliance</h1>
            <p class='sub-text'>Upload your official documents for verification.</p>
        </div>
        """, unsafe_allow_html=True)

# FORM LAYOUT
c1, c2 = st.columns(2, gap="large")

with c1:
    gst_num = st.text_input("GST Registration Number *", placeholder="e.g. 22AAAAA0000A1Z5").upper()
    bank_acc = st.text_input("Bank Account Number *", placeholder="Digits only")
    ifsc = st.text_input("IFSC Code *", placeholder="e.g. SBIN0001234").upper()
    pan_card = st.text_input("PAN Card Number *", placeholder="e.g. ABCDE1234F").upper()

with c2:
    firm_cert = st.file_uploader("Firm Registration Certificate *", type=['pdf', 'jpg', 'png'])
    poa_auth = st.file_uploader("Power of Attorney / Authorization *", type=['pdf', 'jpg', 'png'])
    msme_cert = st.file_uploader("MSME Certificate", type=['pdf', 'jpg', 'png'])
    dpiit_cert = st.file_uploader("DPIIT Certificate", type=['pdf', 'jpg', 'png'])

# NAVIGATION
st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
b_col1, b_col2, b_col3 = st.columns([1, 1, 1])

with b_col1:
    if st.button(" <- Back "):
        st.switch_page("pages/informationCollection_1.py")

with b_col3:
    if st.button(" Next -> "):
        # Validation Checks
        if not gst_num or not is_valid(GST_REGEX, gst_num):
            st.error("Enter a valid GST number.")
            st.stop()
        if not pan_card or not is_valid(PAN_REGEX, pan_card):
            st.error("Enter a valid PAN number.")
            st.stop()
        if not bank_acc.isdigit() or not (9 <= len(bank_acc) <= 18):
            st.error("Bank Account Number must be 9-18 digits.")
            st.stop()
        if not ifsc or not is_valid(IFSC_REGEX, ifsc):
            st.error("Enter a valid IFSC code.")
            st.stop()
        if not firm_cert:
            st.error("Firm Registration Certificate is required.")
            st.stop()
        if not poa_auth:
            st.error("Power of Attorney / Authorization is mandatory.")
            st.stop()

        # 1. GET COMPANY ID
        company_id = st.session_state.get("company_id")
        if not company_id:
            prof_check = supabase.table("profiles").select("company_id").eq("id", user_id).maybe_single().execute()
            company_id = prof_check.data.get("company_id") if prof_check.data else None
            st.session_state["company_id"] = company_id

        # 2. UPLOAD FILES
        with st.spinner("Uploading documents..."):
            firm_cert_path = upload_file(firm_cert, f"firm_certificate_{user_id}")
            poa_path = upload_file(poa_auth, f"poa_authorization_{user_id}")
            msme_path = upload_file(msme_cert, f"msme_certificate_{user_id}")
            dpiit_path = upload_file(dpiit_cert, f"dpiit_certificate_{user_id}")

        # 3. PREPARE PAYLOAD
        compliance_data = {
            "user_id": user_id,
            "company_id": company_id, # LINKING DATA TO COMPANY
            "gst_number": gst_num,
            "bank_account_number": bank_acc,
            "ifsc_code": ifsc,
            "pan_number": pan_card,
            "firm_certificate_url": firm_cert_path,
            "poa_certificate_url": poa_path,
            "msme_certificate_url": msme_path,
            "dpiit_certificate_url": dpiit_path,
        }

        try:
            # 4. SAVE TO DATABASE
            supabase.table("business_compliance").upsert(compliance_data, on_conflict="user_id").execute()

            # 5. ADVANCE STEPS
            supabase.table("profiles").update({"onboarding_step": 3}).eq("id", user_id).execute()
            supabase.table("company_information").update({"onboarding_step": 3}).eq("id", user_id).execute()
            
            st.session_state["onboarding_step"] = 3

            # 6. REDIRECT
            st.switch_page("pages/informationCollection_3.py")
            st.stop()

        except Exception as e:
            st.error(f"Error saving compliance data: {e}")