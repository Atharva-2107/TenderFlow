import streamlit as st
import os
import base64
from pathlib import Path

# PAGE CONFIG
st.set_page_config(page_title="TenderFlow | Compliance", layout="wide")

# UTILS: Robust Base64 Loading
def get_base64_of_bin_file(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        return None
    return None

# --- PREMIUM DARK CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    /* NUCLEAR ANCHOR FIX - Removes the (-) icon */
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

    /* Inputs & Uploaders */
    .stTextInput input, .stFileUploader section {
        background-color: #161925 !important;
        color: #FFFFFF !important;
        border: 1px solid #2d313e !important;
        border-radius: 8px !important;
    }

    /* NEXT BUTTON */
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

# LOGO (Using your preferred positioning)
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
            <h1>Legal & Tax Compliance</h1>
            <p class='sub-text'>Upload your official documents for verification.</p>
        </div>
        """, unsafe_allow_html=True)

# --- FORM LAYOUT ---
c1, c2 = st.columns(2, gap="large")

with c1:
    gst_num = st.text_input("GST Registration Number", placeholder="e.g. 22AAAAA0000A1Z5")
    bank_acc = st.text_input("Bank Account Number", placeholder="Enter Account No.")
    ifsc = st.text_input("IFSC Code", placeholder="e.g. SBIN0001234")
    pan_card = st.text_input("PAN Card Number", placeholder="e.g. ABCDE1234F")

with c2:
    firm_cert = st.file_uploader("Firm Registration Certificate", type=['pdf', 'jpg', 'png'])
    poa_auth = st.file_uploader("Power of Attorney / Authorization", type=['pdf', 'jpg', 'png'])
    msme_cert = st.file_uploader("MSME Certificate (Optional)", type=['pdf', 'jpg', 'png'])
    dpiit_cert = st.file_uploader("DPIIT (Startup) Certificate (Optional)", type=['pdf', 'jpg', 'png'])

# --- ACTION ---
b1, b2, b3 = st.columns([1,1,1])

with b2:
    if st.button(" Finish Setup "):
        st.balloons()
        st.success("Verification documents submitted successfully!")