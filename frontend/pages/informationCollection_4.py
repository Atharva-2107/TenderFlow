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
st.set_page_config(page_title="TenderFlow | Experience", layout="wide")

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

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

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
        # Return existing path if upload fails/file exists
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

    /* BUTTONS */
    div.stButton {
        display: flex;
        justify-content: center;
    }

    div.stButton > button {
        background-color: #7c3aed !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        padding: 12px 60px !important;
        font-weight: 600 !important;
        border: 1.5px solid #8b5cf6 !important;
        margin-top: 20px;
    }

    div.stButton > button:hover {
        background-color: #6d28d9 !important;
        border-color: #7c3aed !important;
    }

    /* Secondary Button Styling (Add Experience) */
    .add-btn-container [data-testid="baseButton-secondaryFormSubmit"] {
        background-color: transparent !important;
        color: #a855f7 !important;
        border: 1px solid #a855f7 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
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

st.markdown("""
        <div class="centered-header">
            <h1>Experience & Past Performance</h1>
            <p class='sub-text'>Showcase your project history and track record.</p>
        </div>
        """, unsafe_allow_html=True)

# 1. GET COMPANY ID
company_id = st.session_state.get("company_id")
if not company_id:
    prof_check = supabase.table("profiles").select("company_id").eq("id", user_id).maybe_single().execute()
    company_id = prof_check.data.get("company_id") if prof_check.data else None
    st.session_state["company_id"] = company_id

# 2. EXPERIENCE FORM
with st.form("experience_form", clear_on_submit=True):
    c1, c2 = st.columns(2, gap="large")
    with c1:
        project_name = st.text_input("Project Name (similar work)")
        client_name = st.text_input("Client Name")
        client_type = st.selectbox("Client Type", ["Govt", "Pvt", "PSU", "Other"])
        work_category = st.selectbox("Work Category", ["Roads", "Service", "IT", "Construction", "Other"])
        scope_of_work = st.text_area("Scope of Work", height=130)

    with c2:
        contract_val = st.text_input("Contract Value")
        comp_date = st.date_input("Completion Date")
        comp_status = st.selectbox("Completion Status", ["Completed", "Ongoing", "Under Maintenance"])
        comp_cert = st.file_uploader("Completion Certificate *", type=['pdf', 'jpg'])
        portfolio = st.file_uploader("Portfolio (optional)", type=['pdf', 'jpg', 'zip'])

    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown('<div class="add-btn-container">', unsafe_allow_html=True)
    _, add_col, _ = st.columns([1, 1.5, 1])
    with add_col:
        add_exp = st.form_submit_button("＋ ADD EXPERIENCE", use_container_width=True)
        if add_exp:
            try:
                if not project_name.strip():
                    st.error("Project Name is required.")
                elif not client_name.strip():
                    st.error("Client Name is required.")
                elif not contract_val.strip():
                    st.error("Contract Value is required.")
                elif not comp_cert:
                    st.error("Completion certificate is mandatory.")
                else:
                    with st.spinner("Saving experience record..."):
                        cert_path = upload_file(comp_cert, f"cert_{project_name.replace(' ', '_')}_{user_id}")
                        portfolio_path = upload_file(portfolio, f"portfolio_{project_name.replace(' ', '_')}_{user_id}")

                        exp_data = {
                            "user_id": user_id,
                            "company_id": company_id, 
                            "project_name": project_name,
                            "client_name": client_name,
                            "client_type": client_type,
                            "work_category": work_category,
                            "scope_of_work": scope_of_work,
                            "contract_value": contract_val,
                            "completion_date": comp_date.isoformat() if comp_date else None,
                            "completion_status": comp_status,
                            "completion_certificate_url": cert_path,
                            "portfolio_url": portfolio_path
                        }

                        supabase.table("experience_records").insert(exp_data).execute()
                        st.success(f"Success! '{project_name}' has been added to the team portfolio.")
            except Exception as e:
                st.error(f"Error saving experience: {e}")

# 3. NAVIGATION
st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
b_col1, b_col2, b_col3 = st.columns([1, 1, 1])

with b_col1:
    if st.button(" <- Back "):
        st.switch_page("pages/informationCollection_3.py")

with b_col3:
    if st.button(" Finish & Go to Dashboard "):
        if not company_id:
            st.error("Missing Company ID. Please go back to step 1 and ensure company is selected.")
            st.stop()
            
        try:
            with st.spinner("Finalizing setup..."):
                # 1. Update Personal Profile (Master Switch)
                # This ensures the login page knows THIS user is done
                profile_update = supabase.table("profiles").update({
                    "onboarding_complete": True,
                    "onboarding_step": 999
                }).eq("id", user_id).execute()
                
                # 2. Update Company Record
                # This ensures the login page knows ANY user from this company can skip setup
                company_update = supabase.table("company_information").update({
                    "onboarding_step": 999,
                    "onboarding_complete": True
                }).eq("company_id", company_id).execute()

                # Verify updates
                if profile_update.data or company_update.data:
                    # Update local session state
                    st.session_state["onboarding_complete"] = True
                    st.session_state["onboarding_step"] = 999
                    
                    st.success("Onboarding Complete! Redirecting...")
                    time.sleep(1)
                    
                    # Redirect
                    st.switch_page("pages/dashboard.py")
                    st.stop()
                else:
                    st.error("Failed to update onboarding status in database. Please check your 'profiles' and 'company_information' tables.")
        except Exception as e:
            st.error(f"Error finalizing setup: {str(e)}")