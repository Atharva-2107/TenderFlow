import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client
import streamlit.components.v1 as components

load_dotenv()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Profile • Tenderflow",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- AUTH GUARD ----------------
if not st.session_state.get("authenticated"):
    st.switch_page("pages/loginPage.py")
    st.stop()

if not st.session_state.get("onboarding_complete"):
    step = st.session_state.get("onboarding_step", 1)
    st.switch_page(f"pages/informationCollection_{step}.py")
    st.stop()

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

# ---------------- THEME CSS ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: radial-gradient(circle at 20% 30%, #1a1c4b 0%, #0f111a 100%);
}
            
header, footer { visibility:hidden; }

/* center width */
.block-container {
    max-width: 1050px;
    padding-top: 1.2rem;
}

/* card */
.tf-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px;
    padding: 16px 18px;
}

.tf-title {
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 2px;
}

.tf-subtitle {
    font-size: 13px;
    color: rgba(255,255,255,0.70);
    margin-bottom: 18px;
}

.tf-card-title {
    font-size: 14px;
    font-weight: 700;
    color: rgba(255,255,255,0.95);
    margin-bottom: 12px;
}

.tf-label {
    font-size: 12px;
    color: rgba(255,255,255,0.60);
    margin-bottom: 3px;
}

.tf-value {
    font-size: 14px;
    font-weight: 650;
    color: rgba(255,255,255,0.95);
}

.tf-badge {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.14);
    font-size: 12px;
    font-weight: 700;
    color: rgba(255,255,255,0.92);
}

.tf-muted {
    font-size: 12px;
    color: rgba(255,255,255,0.55);
}
</style>
""", unsafe_allow_html=True)

# ---------------- HELPERS ----------------
FULL_ACCESS_ROLES = {"Bid Manager", "Executive Manager", "Executive"}

def fetch_company_details(cid: str):
    if not cid:
        return None
    try:
        res = (
            supabase.table("companies")
            .select("id, name, invite_code")
            .eq("id", cid)
            .single()
            .execute()
        )
        return res.data
    except Exception:
        return None

def profile_completion(company_obj: dict):
    checks = {
        "Email Linked": bool(user_email and user_email != "Not available"),
        "Role Assigned": bool(user_role and user_role != "Unknown"),
        "Company Linked": bool(company_obj and company_obj.get("name")),
    }
    completed = sum(1 for _, ok in checks.items() if ok)
    percent = int((completed / len(checks)) * 100)
    return percent, checks

company = fetch_company_details(company_id)
completion_percent, completion_checks = profile_completion(company)
invite_code = (company or {}).get("invite_code")

# ---------------- UI ----------------
st.markdown("<div class='tf-title'>👤 Profile</div>", unsafe_allow_html=True)
st.markdown("<div class='tf-subtitle'>Your account & organization details</div>", unsafe_allow_html=True)

row1_left, row1_right = st.columns([1.4, 1])

with row1_left:
    with st.container():
        st.markdown("<div class='tf-card'>", unsafe_allow_html=True)
        st.markdown("<div class='tf-card-title'>Account Details</div>", unsafe_allow_html=True)

        st.markdown("<div class='tf-label'>Company</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='tf-value'>{(company or {}).get('name', 'Not linked')}</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        st.markdown("<div class='tf-label'>Email</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='tf-value'>{user_email}</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        st.markdown("<div class='tf-label'>Role</div>", unsafe_allow_html=True)
        st.markdown(f"<span class='tf-badge'>{user_role}</span>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

with row1_right:
    with st.container():
        st.markdown("<div class='tf-card'>", unsafe_allow_html=True)
        st.markdown("<div class='tf-card-title'>Profile Completion</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='tf-value'>{completion_percent}%</div>", unsafe_allow_html=True)
        st.progress(completion_percent / 100)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        for item, ok in completion_checks.items():
            st.write(f"{'✅' if ok else '⚠️'} {item}")

        st.markdown("</div>", unsafe_allow_html=True)

# Invite code section
if user_role in FULL_ACCESS_ROLES:
    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='tf-card'>", unsafe_allow_html=True)
        st.markdown("<div class='tf-card-title'>Company Invite Code</div>", unsafe_allow_html=True)
        st.markdown("<div class='tf-muted'>Share this code to onboard users into your company workspace.</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

        if invite_code:
            code_col, btn_col = st.columns([2.2, 1])

            with code_col:
                st.code(invite_code, language="text")

            with btn_col:
                # clean copy button
                components.html(
                    f"""
                    <div style="font-family: Inter, sans-serif;">
                        <button onclick="navigator.clipboard.writeText('{invite_code}')"
                            style="
                                width: 100%;
                                padding: 10px 12px;
                                border-radius: 12px;
                                border: 1px solid rgba(255,255,255,0.18);
                                background: rgba(255,255,255,0.10);
                                color: white;
                                font-weight: 700;
                                cursor: pointer;
                            ">
                            📋 Copy Code
                        </button>
                        <div style="margin-top:8px; font-size:12px; color: rgba(255,255,255,0.55); text-align:center;">
                            One click copy
                        </div>
                    </div>
                    """,
                    height=90
                )
        else:
            st.info("Invite code not available for this company.")

        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

if st.button("⬅ Back to Dashboard"):
    st.switch_page("app.py")
