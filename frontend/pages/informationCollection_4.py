import streamlit as st
import os
import base64
from datetime import date
from pathlib import Path

# PAGE CONFIG
st.toast("Financial details recorded.")
st.set_page_config(page_title="TenderFlow | Experience", layout="wide")

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

    /* Inputs & UI Elements */
    .stTextInput input, .stSelectbox [data-baseweb="select"], .stTextArea textarea, .stDateInput input, .stFileUploader section {
        background-color: #161925 !important;
        color: #FFFFFF !important;
        border: 1px solid #2d313e !important;
        border-radius: 8px !important;
    }

    /* --- THE PURPLE FIX --- */
    /* This targets the button inside your specific container div */
    .finish-btn-container [data-testid="baseButton-secondary"] {
        background-color: #7c3aed !important;
        color: white !important;
        border: 1px solid #8b5cf6 !important;
        padding: 0.5rem 2rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
    }

    .finish-btn-container [data-testid="baseButton-secondary"]:hover {
        background-color: #6d28d9 !important;
        border-color: white !important;
        color: white !important;
    }

    /* Secondary Button Styling (Add Experience) */
    .add-btn-container [data-testid="baseButton-secondary"] {
        background-color: transparent !important;
        color: #a855f7 !important;
        border: 1px solid #a855f7 !important;
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

st.markdown("""
        <div class="centered-header">
            <h1>Experience & Past Performance</h1>
            <p class='sub-text'>Showcase your project history and track record.</p>
        </div>
        """, unsafe_allow_html=True)

# --- FORM ---
with st.form("experience_form", clear_on_submit=True):
    c1, c2 = st.columns(2, gap="large")
    with c1:
        project_name = st.text_input("Project Name (similar work)")
        client_name = st.text_input("Client Name")
        client_type = st.selectbox("Client Type", ["Govt", "Pvt", "PSU", "Other"])
        work_category = st.selectbox("Work Category", ["Roads", "Service", "IT", "Construction", "Other"])
        scope_of_work = st.text_area("Scope of Work (just text)", height=130)

    with c2:
        contract_val = st.text_input("Contract Value")
        comp_date = st.date_input("Completion Date")
        comp_status = st.selectbox("Completion Status", ["Completed", "Ongoing", "Under Maintenance"])
        comp_cert = st.file_uploader("Completion Certificate", type=['pdf', 'jpg'])
        portfolio = st.file_uploader("Portfolio (optional)", type=['pdf', 'jpg', 'zip'])

    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown('<div class="add-btn-container">', unsafe_allow_html=True)
    _, add_col, _ = st.columns([1, 1, 1])
    with add_col:
        # Form submit buttons are slightly different, so we style them separately
        st.form_submit_button("＋ ADD EXPERIENCE", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- FINAL ACTION ---
st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
b1, b2, b3, b4, b5 = st.columns([1,2,1,2,1])

with b2:
    if st.button(" <- Back "):
        # Switch back to the first info page
        st.switch_page("pages/informationCollection_3.py")

with b4:
    if st.button(" Next -> "):
        st.switch_page("pages/dashboard.py")
        st.balloons()
        st.success("Verification documents submitted successfully!")