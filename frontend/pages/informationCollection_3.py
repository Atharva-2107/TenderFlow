import streamlit as st
import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# PAGE CONFIG
st.set_page_config(page_title="TenderFlow | Financial Capacity", layout="wide")
st.toast("Legal & Tax Compliance details recorded.")

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

def upload_file(file, filename):
    if not file:
        return None

    path = f"{user_id}/{filename}"

    supabase.storage.from_("compliance_docs").upload(
        path,
        file.getvalue(),
        {"content-type": file.type}
    )

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


st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    /* NUCLEAR ANCHOR FIX */
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

    /* Inputs & File Uploader Styling */
    .stTextInput input, .stFileUploader section {
        background-color: #161925 !important;
        color: #FFFFFF !important;
        border: 1px solid #2d313e !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
    }

    /* BUTTONS */
    div.stButton {
        display: flex;
        justify-content: center;
    }

    div.stButton > button {
        background-color: #7c3aed !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        padding: 10px 80px !important;
        font-weight: 600 !important;
        border: 1.5px solid #8b5cf6 !important;
        margin-top: 40px;
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
logo_path = current_file_path.parent / "assets" / "logo.png"
logo_base64 = get_base64_of_bin_file(logo_path)

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

st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

b1, b2, b3, b4, b5 = st.columns([1,2,1,2,1])

with b2:
    if st.button(" <- Back "):
        # Switch back to the first info page
        st.switch_page("pages/informationCollection_2.py")

if st.button(" Next -> "):
    try:
        # SAFETY CHECK 
        if not sb_session or not sb_session.access_token:
            st.error("Session expired. Please log in again.")
            st.switch_page("pages/loginPage.py")
            st.stop()

        # UNIQUE FILE NAMES (
        balance_sheet_path = upload_file(
            balance_sheet,
            f"balance_sheet_{user_id}.pdf"
        )
        ca_cert_path = upload_file(
            ca_cert,
            f"ca_certificate_{user_id}.pdf"
        )

        # DATA PAYLOAD 
        data = {
            "user_id": user_id,   
            "avg_annual_turnover": avg_turnover,
            "fy_wise_turnover": fy_wise,
            "balance_sheet_url": balance_sheet_path,
            "ca_certificate_url": ca_cert_path,
        }

        #UPSERT 
        supabase.table("financials") \
            .upsert(data, on_conflict="user_id") \
            .execute()

        supabase.table("profiles") \
            .update({"onboarding_step": 4}) \
            .eq("id", user_id) \
            .execute()

        st.session_state["onboarding_step"] = 4

        # REDIRECT 
        st.switch_page("pages/informationCollection_4.py")
        st.stop()

    except Exception as e:
        st.error(f"Error saving financial data: {e}")

