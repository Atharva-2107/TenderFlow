import streamlit as st
import os
import base64
from datetime import date
from pathlib import Path

# PAGE CONFIG
st.set_page_config(page_title="TenderFlow | Basic Information", layout="wide")

# UTILS: Robust Base64 Loading
def get_base64_of_bin_file(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        return None
    return None

# REFINED DARK CSS 
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    /* HIDE HEADER ANCHOR ICONS (-) */
    button[title="View header anchor"] {
        display: none !important;
    }
    .stHtmlHeader a , .stMarkdown a{
        display: none !important;
    }
    header { visibility: hidden; }
            
    .stApp {
        background-color: #0f111a;
        font-family: 'Inter', sans-serif;
    }

    /* Centered Content Container */
    .block-container {
        padding-top: 2rem !important;
        max-width: 1100px !important;
        margin: auto;
    }
    
    /* Centered Align Header section */
    .centered-header {
            text-align: center;
            width: 100%;
            margin-top: 20px;
    }

    /* Typography */
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
        color: #a855f7 !important; /* Portal Purple */
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Inputs: Portal Style */
    .stTextInput input, .stSelectbox [data-baseweb="select"], .stTextArea textarea, .stDateInput input {
        background-color: #161925 !important;
        color: #FFFFFF !important;
        border: 1px solid #2d313e !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
    }

    /* BUTTONS */
    div.stButton > button {
        background-color: #7c3aed !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        padding: 10px 40px !important;
        font-weight: 600 !important;
        border: 1.5px solid #8b5cf6 !important;
        float: right;
        margin-top: 20px;
    }

    div.stButton > button:hover {
        background-color: #6d28d9 !important;
        border-color: #7c3aed !important;
        /* color: white !important; */
    }

    /* Hide Streamlit elements */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    </style>
    """, unsafe_allow_html=True)

# LOGO RESOLUTION 
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
else:
    st.markdown("<h2 style='color:#a855f7; margin-bottom:20px;'>TenderFlow</h2>", unsafe_allow_html=True)

# --- CONTENT ---
st.markdown("""
        <div class="centered-header">
            <h1>Basic Information</h1>
            <p class='sub-text'>Complete your corporate profile to finish the setup.</p>
        </div>
        """, unsafe_allow_html=True)

# --- FORM LAYOUT ---
c1, c2 = st.columns(2, gap="large")

with c1:
    company_name = st.text_input("Company Name", placeholder="Official name")
    org_type = st.selectbox("Organization Type", ["Pvt. Ltd.", "LLP", "Partnership", "Proprietorship"])
    incorp_date = st.date_input("Date of Incorporation", value=date.today())

with c2:
    email = st.text_input("Work Email", placeholder="name@company.com")
    phone = st.text_input("Phone Number", placeholder="+91")
    designation = st.text_input("Your Designation", placeholder="e.g. Director")

st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
reg_address = st.text_area("Registration Address", height=100)

same_as_reg = st.checkbox("Office address same as registration")
if not same_as_reg:
    office_address = st.text_area("Office Address", height=100)

auth_name = st.text_input("Authorized Signatory Name", placeholder="Full legal name")

# --- ACTION ---
# st.markdown("<hr>", unsafe_allow_html=True)
b1, b2, b3 = st.columns([2, 1, 2])
with b2: 
    if st.button(" Next -> "):
        # This switches to the second file in your pages folder
        st.switch_page("pages/informationCollection_2.py")
        # st.toast("Basic Information recorded.")