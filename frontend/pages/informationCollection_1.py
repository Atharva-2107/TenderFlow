#from requests import session
import streamlit as st
import os
import base64
from datetime import date
from pathlib import Path
from supabase import create_client
import supabase
import re

if not st.session_state.get("authenticated"):
    st.switch_page("pages/loginPage.py")
    st.stop()

if st.session_state.get("onboarding_complete"):
    st.switch_page("pages/dashboard.py")
    st.stop()
    
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
supabase.postgrest.auth(sb_session.access_token)

if "user" not in st.session_state:
    # Not logged in at all
    st.switch_page("pages/loginPage.py")
    st.stop()

# If onboarding already done → dashboard
if "user" not in st.session_state or st.session_state["user"] is None:
    st.error("Session expired. Please log in again.")
    st.switch_page("pages/loginPage.py")
    st.stop()

user = st.session_state["user"]
user_id = user.id

# UTILS
def get_base64_of_bin_file(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        return None
    return None

#cSs
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    button[title="View header anchor"] { display: none !important;}
    .stHtmlHeader a , .stMarkdown a{ display: none !important;}
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
        <div style="position: absolute; left: -200px; top: -20px;">
            <img src="data:image/png;base64,{logo_base64}" width="190">
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<h2 style='color:#a855f7; margin-bottom:20px;'>TenderFlow</h2>", unsafe_allow_html=True)

# header
st.markdown("""
        <div class="centered-header">
            <h1>Basic Information</h1>
            <p class='sub-text'>Complete your corporate profile to finish the setup.</p>
        </div>
        """, unsafe_allow_html=True)

# FORM inputs
c1, c2 = st.columns(2, gap="large")

with c1:
    company_name = st.text_input("Company Name", placeholder="Official name", max_chars=50)
    org_type = st.selectbox("Organization Type", ["Pvt. Ltd.", "LLP", "Partnership", "Proprietorship"])
    incorp_date = st.date_input("Date of Incorporation", value=date.today(), max_value=date.today())

with c2:
    email = st.text_input("Work Email", placeholder="name@company.com")
    phone = st.text_input("Phone Number", placeholder="+91",max_chars=10)
    designation = st.text_input("Your Designation", placeholder="e.g. Director",max_chars=25)

st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
reg_address = st.text_area("Registration Address", height=100, max_chars=300)

same_as_reg = st.checkbox("Office address same as registration")
if not same_as_reg:
    office_address = st.text_area("Office Address", height=100)

auth_name = st.text_input("Authorized Signatory Name", placeholder="Full legal name")

#validation 
EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"
PHONE_REGEX = r"^\+91[6-9]\d{9}$"

def is_valid_email(email):
    return re.match(EMAIL_REGEX, email)

def is_valid_phone(phone):
    return re.match(PHONE_REGEX, phone)

# ACTION JACKSON BEEBEE BEEE..
st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
b1, b2, b3 = st.columns([2, 1, 2])

with b2:
    if st.button(" Next -> "):

        # Validations
        if not company_name.strip():
            st.error("company NAme required!")
            st.stop()

        if len(company_name) < 3:
            st.error("Company name must be atleast 3 chars")
            st.stop()

        if not email or not is_valid_email(email):
            st.error("Please enter a valid email id.")
            st.stop()

        if phone and not is_valid_phone(phone):
            st.error("Phone number must be in format +91XXXXXXXXXX")
            st.stop()

        if not reg_address and not office_address.strip():
            st.error("Office Address required.")
            st.stop()

        if not auth_name.strip():
            st.error("Authorized Signatory name is required.")
            st.stop()

        if len(auth_name) < 3:
            st.error("Authorized Signatory name must have atleast 3 chars.")
            st.stop()

        # Prepare payload
        profile_data = {
            "id": user_id,  # auth.users.id
            "company_name": company_name,
            "org_type": org_type,
            "incorp_date": str(incorp_date),
            "email": email,
            "phone_number": phone,
            "designation": designation,
            "reg_address": reg_address,
            "office_address": reg_address if same_as_reg else office_address,
            "authorized_signatory": auth_name,
            "onboarding_step": 2
        }

        try:
            # UPSERT (SAFE)
            supabase.table("profiles") \
                .upsert(profile_data, on_conflict="id") \
                .execute()

            # Update session
            st.session_state["onboarding_step"] = 2

            # Redirect
            st.switch_page("pages/informationCollection_2.py")
            st.stop()

        except Exception as e:
            st.error(f"Error saving data: {e}")
