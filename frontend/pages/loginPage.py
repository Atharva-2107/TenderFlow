import streamlit as st
import os
import base64
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client
from streamlit_cookies_manager import EncryptedCookieManager

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="TenderFlow AI | Login", layout="wide")

# -------------------------------------------------
# ROBUST .ENV LOADER (SEARCHES UPWARD)
# -------------------------------------------------
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

# -------------------------------------------------
# COOKIE MANAGER (AUTO 7-DAY LOGIN)
# -------------------------------------------------
cookies = EncryptedCookieManager(
    prefix="tenderflow_",
    password="CHANGE_THIS_SECRET"
)

if not cookies.ready():
    st.stop()

def login_user(email: str):
    cookies["logged_in"] = "true"
    cookies["user_email"] = email
    cookies["expiry"] = (datetime.utcnow() + timedelta(days=7)).isoformat()
    cookies.save()

def is_logged_in() -> bool:
    if cookies.get("logged_in") == "true":
        expiry = cookies.get("expiry")
        return expiry and datetime.utcnow() < datetime.fromisoformat(expiry)
    return False

if is_logged_in():
    st.switch_page("pages/dashboard.py")

# -------------------------------------------------
# UTILS
# -------------------------------------------------
def get_base64_of_bin_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# -------------------------------------------------
# THEME (UNCHANGED)
# -------------------------------------------------
def inject_exact_brand_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    .stApp {
        background-color:#0f111a;
        font-family:'Inter',sans-serif;
    }

    header, footer { visibility:hidden; }
    .block-container { padding:0 !important; }

    .stApp::before {
        content:"";
        position:fixed;
        top:0; left:0;
        width:50vw; height:100vh;
        background:linear-gradient(rgba(11,17,23,.85), rgba(11,17,23,.95));
        border-right:1px solid rgba(255,255,255,.05);
        z-index:0;
    }
    </style>
    """, unsafe_allow_html=True)

inject_exact_brand_theme()

# -------------------------------------------------
# LAYOUT
# -------------------------------------------------
col_branding, col_login = st.columns([1.2, 1])

# LEFT BRANDING
with col_branding:
    st.markdown("<div style='height:30vh'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div style='padding-left:15%'>
            <h1 style='color:white;font-size:60px;font-weight:800;line-height:1'>
                TenderFlow<br>
                <span style='color:#D4AF37'>Intelligence.</span>
            </h1>
            <p style='color:#94a3b8;font-size:18px;margin-top:25px'>
                Proprietary AI for procurement.
            </p>
        </div>
    """, unsafe_allow_html=True)

# RIGHT LOGIN
with col_login:
    st.markdown("<div style='height:18vh'></div>", unsafe_allow_html=True)
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

        # -------------------------
        # EMAIL LOGIN
        # -------------------------
        with st.form("login_form"):
            email = st.text_input("Work Email")
            password = st.text_input("Password", type="password")

            submit = st.form_submit_button("Enter Portal")

            if submit:
                try:
                    res = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })

                    if res.user:
                        login_user(email)
                        st.switch_page("pages/dashboard.py")
                    else:
                        st.error("Invalid credentials")
                except Exception:
                    st.error("Login failed")

        # -------------------------
        # GOOGLE LOGIN (SUPABASE)
        # -------------------------
        st.markdown("<div style='margin-top:25px'></div>", unsafe_allow_html=True)

        oauth = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": "http://localhost:8501"
            }
        })

        st.markdown(f"""
        <a href="{oauth.url}">
            <button style="
                width:100%;
                padding:14px;
                border-radius:50px;
                background:#111827;
                color:white;
                border:1px solid #2d313e;
                font-size:16px;
                margin-top:10px;">
                Continue with Google
            </button>
        </a>
        """, unsafe_allow_html=True)

        st.markdown(
            "<p style='text-align:center;color:#2d313e;font-size:10px;margin-top:50px'>AUTHORISED PERSONNEL ONLY</p>",
            unsafe_allow_html=True
        )
