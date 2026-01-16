import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from supabase import create_client
import base64
import os
from pathlib import Path

def get_base64_of_bin_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# SETTINGS & AUTH 
load_dotenv()
st.set_page_config(page_title="Profile • Tenderflow", page_icon="👤", layout="wide")

# ---------------- AUTH GUARD ----------------
if not st.session_state.get("authenticated"):
    st.switch_page("pages/loginPage.py")
    st.stop()

if not st.session_state.get("onboarding_complete"):
    step = st.session_state.get("onboarding_step", 1)
    st.switch_page(f"pages/informationCollection_{step}.py")
    st.stop()

# ---------------- SESSION DATA ----------------
user_obj = st.session_state.get("user")
user_role = st.session_state.get("user_role", "Unknown")
company_id = st.session_state.get("company_id")

# ---------------- SUPABASE ----------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase environment variables not loaded")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- USER SAFE CONVERSION ----------------
if user_obj is None:
    user = {}
elif isinstance(user_obj, dict):
    user = user_obj
else:
    try:
        user = user_obj.model_dump()
    except Exception:
        try:
            user = user_obj.__dict__
        except Exception:
            user = {}

user_email = user.get("email", "Not available")

# ---------------- FETCH COMPANY DETAILS (DB) ----------------
company_name = "Not linked"
invite_code = None

if company_id:
    try:
        res = (
            supabase.table("companies")
            .select("name, invite_code")
            .eq("id", company_id)
            .single()
            .execute()
        )
        if res.data:
            company_name = res.data.get("name", "Not linked")
            invite_code = res.data.get("invite_code")
    except Exception:
        pass

# ---------------- PROFILE COMPLETION (DYNAMIC) ----------------
completion_checks = {
    "Email Linked": bool(user_email and user_email != "Not available"),
    "Role Assigned": bool(user_role and user_role != "Unknown"),
    "Company Linked": bool(company_name and company_name != "Not linked"),
}

completion_percent = int((sum(completion_checks.values()) / len(completion_checks)) * 100)

# CLEAN PREMIUM CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Montserrat:wght@800&display=swap');

html, body, [class*="css"] { 
    font-family: 'Inter', sans-serif; 
}

.stApp {
    background: radial-gradient(circle at top right, #1e2251, #090a11);
}

header { visibility: hidden; }
            
.block-container {
    padding-top: 0.6rem !important;
}

/* HEADER NAV CONTAINER */
.header-nav {
    background: linear-gradient(
        135deg,
        rgba(255,255,255,0.08),
        rgba(255,255,255,0.02)
    );
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px;
    padding: 12px 18px;
    margin-bottom: 22px;
}            


/* Glass Card */
.profile-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 20px;
    padding: 26px;
    backdrop-filter: blur(18px);
    box-shadow: 0 18px 35px rgba(0,0,0,0.35);
}

/* Header */
.page-title {
    color: white;
    font-size: 22px;
    font-weight: 700;
    margin: 0;
}

.page-subtitle {
    color: rgba(255,255,255,0.55);
    font-size: 15px;
    margin-top: 8px;
    margin-bottom: -5px;
}

/* Labels & Values */
.section-label {
    color: rgba(255, 255, 255, 0.45);
    font-size: 15px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}

.data-value {
    color: rgba(255,255,255,0.95);
    font-size: 17px;
    font-weight: 600;
    margin-bottom: 20px;
}

/* Role Badge */
.role-badge {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.14);
    color: rgba(255,255,255,0.92);
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 15px;
    font-weight: 700;
    display: inline-block;
}

/* Right side divider */
.right-panel {
    border-left: 1px solid rgba(255,255,255,0.10);
    padding-left: 18px;
}

/* Small helper text */
.muted {
    color: rgba(255,255,255,0.55);
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

left,  = st.columns([3])

with left:
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
    logo = get_base64_of_bin_file(logo_path)

    if logo:
        st.markdown(f"""
            <div style="display:flex; align-items:center;">
                <img src="data:image/png;base64,{logo}" width="190">
            </div>
        """, unsafe_allow_html=True)

#HEADER ROW 
h1, h2 = st.columns([4, 1])

with h1:
    st.markdown("<h1 class='page-title'>👤 Profile</h1>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Your account & organization details</div>", unsafe_allow_html=True)

with h2:
    st.write("")
    st.write("")
    if st.button("⬅ Back", use_container_width=True):
        st.switch_page("app.py")

st.write("")

# --- MAIN CARD ---
# st.markdown("<div class='profile-card'>", unsafe_allow_html=True)
st.markdown("<div> <hr> </div>", unsafe_allow_html=True)

col1, col2 = st.columns([1.5, 1], gap="large")

# LEFT SIDE
with col1:
    st.markdown("<div class='section-label'>Organization</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='data-value'>{company_name}</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-label'>Email Address</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='data-value'>{user_email}</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-label'>System Role</div>", unsafe_allow_html=True)
    st.markdown(f"<span class='role-badge'>{user_role}</span>", unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # Invite Code
    st.markdown("<div class='section-label'>Workspace Invite Code</div>", unsafe_allow_html=True)
    st.markdown("<div class='muted'>Share this code to onboard team members.</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    code_col, btn_col = st.columns([2.2, 1])

    with code_col:
        st.code(invite_code if invite_code else "Not available", language="text")

    with btn_col:
        components.html(
            f"""
            <button onclick="navigator.clipboard.writeText('{invite_code if invite_code else ""}')"
            style="
                width:100%;
                height:40px;
                cursor:pointer;
                background: rgba(255,255,255,0.12);
                border: 1px solid rgba(255,255,255,0.18);
                border-radius:10px;
                color:white;
                font-weight:700;
                font-size:13px;
                font-family: Inter, sans-serif;
            ">
            📋 Copy
            </button>
            """,
            height=50
        )

# RIGHT SIDE
with col2:
    st.markdown("<div class='right-panel'>", unsafe_allow_html=True)

    st.markdown("<div class='section-label'>Profile Completion</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:white; font-size:22px; font-weight:800; margin-bottom:6px;'>{completion_percent}%</div>", unsafe_allow_html=True)
    st.progress(completion_percent / 100)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='muted'>Complete your onboarding details for better access.</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # end card
