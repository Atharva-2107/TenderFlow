import streamlit as st
import os
import base64
import random
import string
from datetime import datetime
import time
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# PAGE CONFIG
st.set_page_config(page_title="TenderFlow AI | Sign Up", layout="wide")

# LOAD .ENV 
def load_env():
    current = Path(__file__).resolve()
    for parent in current.parents:
        env_path = parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            return True
    return False

if not load_env():
    st.error(".env file not found")
    st.stop()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase environment variables not loaded")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# UTILS
def get_base64_of_bin_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def generate_invite_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# CSS (UNTOUCHED UI)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

.stApp {
    background-color:#0f111a;
    font-family:'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

header, footer { visibility:hidden; }
.block-container { padding:0 !important; }

.stApp::before {
    content:"";
    position:fixed;
    top:0; left:0;
    width:50vw; height:100vh;
    background:radial-gradient(circle at 20% 30%, #1a1c4b 0%, #0f111a 100%);
    border-right:1px solid rgba(255,255,255,.05);
    z-index:0;
}

div[data-testid="stFormSubmitButton"] > button {
    background-color: #7c3aed !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    height: 40px !important;
    min-height: 40px !important;
    max-height: 40px !important;
    min-width: 200px !important;
    padding: 0 24px !important;
    line-height: 40px !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    border: 1.5px solid #8b5cf6 !important;
}

div[data-testid="stFormSubmitButton"] {
    display: flex !important;
    justify-content: center !important;
}
</style>
""", unsafe_allow_html=True)

# LAYOUT
col_branding, col_signup = st.columns([1.2, 1])

# LEFT BRANDING (UNTOUCHED UI)
with col_branding:
    st.markdown("<div style='height:30vh'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div style='padding-left:15%'>
            <h1 style='color:white;font-size:60px;font-weight:800;line-height:1'>
                TenderFlow<br>
                <span style='color:#a855f7'>Intelligence.</span>
            </h1>
            <p style='color:#94a3b8;font-size:18px;margin-top:25px'>
                Proprietary AI for procurement.
            </p>
        </div>
    """, unsafe_allow_html=True)

# RIGHT SIGNUP
with col_signup:
    st.markdown("<div style='height:2vh'></div>", unsafe_allow_html=True)
    _, box, _ = st.columns([0.15, 0.7, 0.15]) # Adjusted slightly for extra fields

    with box:
        logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
        logo = get_base64_of_bin_file(logo_path)

        if logo:
            st.markdown(f"""
                <div style="text-align:center;margin-bottom:14px;">
                    <img src="data:image/png;base64,{logo}" width="240">
                </div>
                <div style="text-align:center;margin-bottom:25px;">
                    <p style="color:#6366f1;font-size:11px;letter-spacing:4px;font-weight:700;">
                        CREATE ACCOUNT
                    </p>
                </div>
            """, unsafe_allow_html=True)

        # SIGN UP FORM
        with st.form("signup_form"):
            email = st.text_input("Work Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            # --- RBAC & MULTI-TENANCY FIELDS ---
            role = st.selectbox("Designation", ["Bid Manager", "Risk Reviewer", "Executive", "Procurement Officer"])
            
            team_choice = st.radio("Team Setup", ["Create New Team", "Join Existing Team"], horizontal=True)
            
            if team_choice == "Create New Team":
                company_name = st.text_input("Company Name")
                invite_code_input = ""
            else:
                company_name = ""
                invite_code_input = st.text_input("Invite Code", placeholder="Ask your manager for the code")

            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 1, 1])
            with c2:
                submit = st.form_submit_button("Create Account", type="primary")

        if submit:
            if not email or not password or not confirm_password:
                st.error("All fields are required")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters")
            elif team_choice == "Create New Team" and not company_name:
                st.error("Company Name is required to create a team")
            elif team_choice == "Join Existing Team" and not invite_code_input:
                st.error("Invite Code is required to join a team")
            else:
                try:
                    # 1. Sign up the user in Supabase Auth
                    res = supabase.auth.sign_up({
                        "email": email.strip(),
                        "password": password
                    })
                    
                    if res.user:
                        user_id = res.user.id
                        company_id = None
                        final_invite_code = ""

                        # 2. HANDLE COMPANY LOGIC
                        if team_choice == "Create New Team":
                            final_invite_code = generate_invite_code()
                            comp_res = supabase.table("companies").insert({
                                "name": company_name,
                                "invite_code": final_invite_code
                            }).execute()
                            if comp_res.data:
                                company_id = comp_res.data[0]['id']
                        else:
                            # Join existing
                            comp_check = supabase.table("companies").select("id").eq("invite_code", invite_code_input.strip()).execute()
                            if comp_check.data:
                                company_id = comp_check.data[0]['id']
                            else:
                                st.error("Invalid Invite Code. Please verify with your team.")
                                st.stop()

                        # 3. CREATE USER PROFILE (RBAC)
                        supabase.table("profiles").insert({
                            "id": user_id,
                            "email": email.strip(),
                            "role": role,
                            "company_id": company_id
                        }).execute()

                        # 4. Sign in to get session
                        login_res = supabase.auth.sign_in_with_password({
                            "email": email.strip(),
                            "password": password
                        })
                
                        if login_res.session:
                            st.session_state["sb_session"] = login_res.session
                            st.session_state["user"] = login_res.user
                            st.session_state["user_role"] = role
                            st.session_state["company_id"] = company_id
                            st.session_state["authenticated"] = True

                            if team_choice == "Create New Team":
                                st.success(f"Team Created! Your Invite Code is: {final_invite_code}")
                                time.sleep(2) # type: ignore

                            st.switch_page("pages/informationCollection_1.py")  
                        else:
                            st.info("Account created. Please verify your email and log in.")
                except Exception as e:
                    st.error(f"Sign up failed: {e}")

        # NAVIGATION (UNTOUCHED UI)
        st.markdown("""
        <div style="text-align:center; margin-top:4px;">
        Already have an account?
        <a href="?go_login=true"
            style="font-size:17px;color:#6366f1;font-weight:500;text-decoration:none;">
        Login
        </a>
        </div>
        """, unsafe_allow_html=True)

        if st.query_params.get("go_login") == "true":
            st.switch_page("pages/loginPage.py")