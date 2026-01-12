import streamlit as st
import os
import base64
import datetime
import time
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# PAGE CONFIG
st.set_page_config(page_title="TenderFlow AI | Login", layout="wide")

# redirect already logged in users
if st.session_state.get("authenticated"):
    st.switch_page("pages/dashboard.py")
    st.stop()

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


# THEME + CSS
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
    line-height: 40px !important;
    padding: 0 18px !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    border: 1.5px solid #8b5cf6 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
}

div[data-testid="stFormSubmitButton"] {
    display: flex !important;
    justify-content: center !important;
}

.signup-text {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
    font-size: 14px;
    color: #94a3b8;
    margin-top: -10px;
}

.signup-text a {
    color: #6366f1;
    text-decoration: none;
    font-weight: 600;
}

.signup-text a:hover {
    text-decoration: underline;
}
</style>
""", unsafe_allow_html=True)

# LAYOUT
col_branding, col_login = st.columns([1.2, 1])

# LEFT BRANDING
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

# RIGHT LOGIN
with col_login:
    st.markdown("<div style='height:2vh'></div>", unsafe_allow_html=True)
    _, box, _ = st.columns([0.2, 0.6, 0.2])

    with box:
        logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
        logo = get_base64_of_bin_file(logo_path)

        if logo:
            st.markdown(f"""
                <div style="text-align:center;margin-bottom:14px;">
                    <img src="data:image/png;base64,{logo}" width="280">
                </div>
                <div style="text-align:center;margin-bottom:35px;">
                    <p style="color:#6366f1;font-size:12px;letter-spacing:4px;font-weight:700;">
                        SECURE ACCESS PORTAL
                    </p>
                </div>
            """, unsafe_allow_html=True)

        # LOGIN FORM
        with st.form("login_form"):
            email = st.text_input("Work Email")
            password = st.text_input("Password", type="password")

            c1, c2, c3 = st.columns([1, 1, 1])
            with c2:
                submit = st.form_submit_button("Enter Portal", type="primary")
        if submit:
            if not email or not password:
                st.error("Email and password are required")
            else:
                try:
                    res = supabase.auth.sign_in_with_password({
                        "email": email.strip(),
                        "password": password
                        })
                    if res.session:
                        # 1. SET BASIC SESSION
                        st.session_state["sb_session"] = res.session
                        st.session_state["user"] = res.user
                        st.session_state["authenticated"] = True

                        # 2. FETCH PROFILE DATA
                        prof_query = supabase.table("profiles").select("role, company_id, onboarding_complete, onboarding_step").eq("id", res.user.id).execute()
                        
                        user_data = prof_query.data[0] if prof_query.data else {}
                        
                        user_role = user_data.get('role', "Team Member")
                        company_id = user_data.get('company_id')
                        is_complete = bool(user_data.get('onboarding_complete', False))
                        current_step = int(user_data.get('onboarding_step', 1))
                        
                        st.session_state["user_role"] = user_role
                        st.session_state["company_id"] = company_id
                        st.session_state["onboarding_complete"] = is_complete

                        # 3. PRIORITY CHECK: IS PROFILE DONE?
                        if is_complete:
                            st.success("Login Successful. Redirecting...")
                            time.sleep(0.5)
                            st.switch_page("pages/dashboard.py")
                            st.stop()

                        # 4. SECONDARY CHECK: IS COMPANY DONE? (For Joiners)
                        company_onboarded = False
                        if company_id:
                            try:
                                # We check if ANY info exists for this company_id.
                                # RLS policy must allow 'select' on company_information for authenticated users in the same company.
                                comp_query = supabase.table("company_information").select("id", count="exact").eq("company_id", company_id).execute()
                                if comp_query.data: 
                                    company_onboarded = True
                            except:
                                pass

                        if company_onboarded:
                            # IMPORTANT FIX: If company is onboarded, updating the user's profile to skip this check next time
                            try:
                                supabase.table("profiles").update({"onboarding_complete": True, "onboarding_step": 999}).eq("id", res.user.id).execute()
                                st.session_state["onboarding_complete"] = True
                            except:
                                pass # proceed anyway
                                
                            st.success("Company Verified. Redirecting...")
                            time.sleep(0.5)
                            st.switch_page("pages/dashboard.py")
                            st.stop()

                        # 5. IF WE ARE HERE, ONBOARDING IS TRULY INCOMPLETE
                        # Define Admin/Creator roles that MUST fill the form
                        admin_roles = ["Executive", "Bid Manager", "Admin"]
                        
                        if user_role in admin_roles:
                            st.warning(f"Setup incomplete. Resuming Step {current_step}...")
                            time.sleep(1)
                            if current_step > 1:
                                st.switch_page(f"pages/informationCollection_{current_step}.py")
                            else:
                                st.switch_page("pages/informationCollection_1.py")
                        else:
                            # Team members (Risk Reviewers, etc.) cannot fill the form.
                            # They should go to dashboard even if "company_information" is missing (read-only view)
                            # to avoid getting stuck in a loop.
                            st.info("ℹ️ Waiting for Admin Setup. Entering View-Only Mode...")
                            time.sleep(2)
                            st.switch_page("pages/dashboard.py")

                    else:
                        st.error("Invalid email or password")

                except Exception as e:
                    st.error(f"Login failed: {str(e)}")
        
        # NAVIGATION LINK
        st.markdown("""
            <div style="text-align:center; margin-top:4px;">
            Don't have an account?
            <a href="?go_signUp=true" target="_self"
            style="
            font-size:17px;
            color:#6366f1;
            font-weight:500;
            text-decoration:none;
            cursor:pointer;
            ">
            SignUp
            </a>
            </div>
        """, unsafe_allow_html=True)

        # REDIRECTION LOGIC
        # We check query params, clear them, and switch page
        if st.query_params.get("go_signUp") == "true":
            st.query_params.clear()  # Clear params to prevent loops
            st.switch_page("pages/signupPage.py")

        st.markdown("""
            <p style='text-align:center;color:#2d313e;font-size:10px;margin-top:50px'>
            AUTHORISED PERSONNEL ONLY
            </p>
        """, unsafe_allow_html=True)