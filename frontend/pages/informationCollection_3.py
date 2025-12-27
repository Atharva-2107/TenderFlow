import streamlit as st
import os
import base64
from pathlib import Path

# PAGE CONFIG
st.set_page_config(page_title="TenderFlow | Financial Capacity", layout="wide")

# UTILS: Robust Base64 Loading
def get_base64_of_bin_file(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        return None
    return None

# --- REFINED PREMIUM DARK CSS ---
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

    /* CENTERED BUTTON */
    div.stButton {
        display: flex;
        justify-content: center;
    }

    div.stButton > button {
        background-color: #7c3aed !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        padding: 12px 80px !important;
        font-weight: 600 !important;
        border: 1.5px solid #8b5cf6 !important;
        margin-top: 50px;
    }

    div.stButton > button:hover {
        background-color: #6d28d9 !important;
        border-color: #7c3aed !important;
    }

    footer {visibility: hidden;}
    
    </style>
    """, unsafe_allow_html=True)

# LOGO (Keeping your positioning)
current_file_path = Path(__file__).resolve()
logo_path = current_file_path.parent / "assets" / "logo.png"
logo_base64 = get_base64_of_bin_file(logo_path)

if logo_base64:
    st.markdown(f"""
        <div style="position: absolute; left: -250px; top: -20px;">
            <img src="data:image/png;base64,{logo_base64}" width="190">
        </div>
    """, unsafe_allow_html=True)

# --- CONTENT ---
st.markdown("""
        <div class="centered-header">
            <h1>Financial Capacity</h1>
            <p class='sub-text'>Please provide turnover details and supporting audit documents.</p>
        </div>
        """, unsafe_allow_html=True)

# --- BALANCED LAYOUT TO PREVENT "EMPTY" LOOK ---
c1, c2 = st.columns(2, gap="large")

with c1:
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    avg_turnover = st.text_input("Average Annual Turnover (Last 3 FY)", placeholder="Enter amount in Lakhs/Crores")
    
    st.markdown("<br>", unsafe_allow_html=True)
    fy_wise = st.text_area("FY Wise Turnover Details", placeholder="e.g. FY23: 50L, FY22: 45L...", height=155)

with c2:
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    balance_sheet = st.file_uploader("Upload Audited Balance Sheet", type=['pdf'])
    
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    ca_cert = st.file_uploader("Upload CA Certificate", type=['pdf'])

# --- ACTION ---
st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
b1, b2, b3 = st.columns([1,1,1])

with b2: 
    if st.button(" Next Step -> "):
        st.toast("Financial details recorded.")