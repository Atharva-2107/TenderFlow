import streamlit as st
import os
import base64
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
from streamlit_cookies_manager import EncryptedCookieManager

# PAGE CONFIG
st.set_page_config(page_title="TenderFlow AI | Sign Up", layout="wide")

# LOAD .ENV (ROBUST)
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

# COOKIE MANAGER
cookies = EncryptedCookieManager(
    prefix="tenderflow_",
    password="CHANGE_THIS_SECRET"
)

if not cookies.ready():
    st.stop()

def login_user(email):
    cookies["logged_in"] = "true"
    cookies["user_email"] = email
    cookies["expiry"] = (datetime.utcnow() + timedelta(days=7)).isoformat()
    cookies.save()

# UTILS
def get_base64_of_bin_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# THEME + CSS (UNCHANGED)
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

/* SUBMIT BUTTON */
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
    white-space: nowrap !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
}

div[data-testid="stFormSubmitButton"] {
    display: flex !important;
    justify-content: center !important;
}

/* SIGN UP TEXT */
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
            

/* LOGIN BUTTON AS LINK (ONLY THIS BUTTON) */
.login-link {
    display: flex;
    justify-content: center;
}

.login-link [data-testid="stBaseButton-secondary"] button {
    background: none !important;
    border: none !important;
    box-shadow: none !important;

    padding: 0 !important;
    margin-top: 4px !important;

    color: #6366f1 !important;
    font-size: 13px !important;   /* slightly smaller */
    font-weight: 500 !important;

    height: auto !important;
    min-height: auto !important;
    line-height: normal !important;

    cursor: pointer !important;
}

.login-link [data-testid="stBaseButton-secondary"] button:hover {
    text-decoration: underline !important;
}



</style>
""", unsafe_allow_html=True)

# LAYOUT
col_branding, col_signup = st.columns([1.2, 1])

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

# RIGHT SIGNUP
with col_signup:
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
                        CREATE ACCOUNT
                    </p>
                </div>
            """, unsafe_allow_html=True)

        # SIGN UP FORM
        with st.form("signup_form"):
            email = st.text_input("Work Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")

            c1, c2, c3 = st.columns([1, 1, 1])
            with c2:
                submit = st.form_submit_button("Create Account", type="primary")

            if submit:
                if password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    try:
                        res = supabase.auth.sign_up({
                            "email": email,
                            "password": password
                        })
                        if res.user:
                            st.success("Account created successfully. Please check your email.")
                        else:
                            st.error("Sign up failed")
                    except Exception:
                        st.error("Sign up failed")

        # 🔥 FIXED NAVIGATION
        st.markdown("""
        <div style="text-align:center; margin-top:4px;">
        Already have an account?
        <a href="?go_login=true"
        style="
            font-size:17px;
            color:#6366f1;
            font-weight:500;
            text-decoration:none;
            cursor:pointer;
       ">
        Login
        </a>
        </div>
        """, unsafe_allow_html=True)

# Handle navigation
    if st.query_params.get("go_login") == "true":
        st.switch_page("pages/loginPage.py")



        # GOOGLE SIGN UP
    oauth = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": "http://localhost:8501"
            }
        })

    st.markdown(f"""
        <a href="{oauth.url}" style="text-decoration:none;">
            <div style="
            width:260px;              /* 👈 controls button width */
            padding:14px;
            border-radius:50px;
            background:#111827;
            color:white;
            border:1px solid #2d313e;
            font-size:16px;
            margin:10px auto 30px;    /* 👈 centers horizontally */
            display:flex;
            justify-content:center;
            align-items:center;">
            Continue with Google
            </div>
        </a>
        """, unsafe_allow_html=True)
