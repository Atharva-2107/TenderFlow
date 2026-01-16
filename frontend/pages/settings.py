import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

st.set_page_config(
    page_title="Settings • Tenderflow",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# AUTH GUARD
if not st.session_state.get("authenticated"):
    st.switch_page("pages/loginPage.py")
    st.stop()

if not st.session_state.get("onboarding_complete"):
    step = st.session_state.get("onboarding_step", 1)
    st.switch_page(f"pages/informationCollection_{step}.py")
    st.stop()

user_obj = st.session_state.get("user")
user_role = st.session_state.get("user_role", "Unknown")


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

company_id = st.session_state.get("company_id")

# SUPABASE
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase environment variables not loaded")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
 
# Fetch company details
company_name = "Not linked"
if company_id:
    try:
        res = (
            supabase.table("companies")
            .select("name")
            .eq("id", company_id)
            .single()
            .execute()
        )
        if res.data:
            company_name = res.data.get("name", "Not linked")
    except Exception:
        pass

# Environment (optional)
APP_ENV = os.getenv("APP_ENV", "production-v1.0")

# Verified status (Supabase auth users often have email_confirmed_at)
verified = bool(user.get("email_confirmed_at"))

# Access Level text based on role
access_level = f"{user_role}" if user_role else "Unknown"

   
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.stApp {
    background: radial-gradient(circle at 2%, 10%, #1a1c4b 0%, #090a11 100%);
}

/* Constrain the width for a professional look */
.block-container {
    max-width: 900px !important;
    padding-top: 3rem !important;
}

/* Glass Card */
.glass-card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(15px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 24px;
    padding: 15px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

.page-title {
    font-size: 32px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.5px;
}

.page-subtitle {
    font-size: 16px;
    color: rgba(255,255,255,0.5);
    margin-bottom: 30px;
}

/* Labels and Inputs */
label {
    color: rgba(255,255,255,0.6) !important;
    font-size: 16px !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

div[data-baseweb="input"] {
    background-color: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
}

/* Primary Button Styling */
div.stButton > button:first-child {
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 12px;
    padding: 10px 24px;
    font-weight: 600;
    width: 100%;
    transition: all 0.3s ease;
}


/* Secondary/Back Button Styling */
div.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.05);
    color: white;
    border: 1px solid rgba(255,255,255,0.1);
}
            
/* Fix only the Back button width so it doesn't become a tall thin pill */
div[data-testid="stButton"] button[kind="secondary"] {
    width: auto !important;
    white-space: nowrap !important;
}

/* Specifically target our back button by key container */
div[data-testid="stButton"] > button:has(span:contains("Back to Dashboard")) {
    width: auto !important;
}

</style>
""", unsafe_allow_html=True)

# Header Section
st.markdown("<div class='page-title'>⚙ Account Settings</div>", unsafe_allow_html=True)
st.markdown("<div class='page-subtitle'>Manage your professional identity on Tenderflow</div>", unsafe_allow_html=True)

# Main Content Grid
left, right = st.columns([1.8, 1], gap="large")

with left:
    st.markdown("""<div style="margin-bottom:-5px; padding-bottom:0px;"><hr style="margin:0; padding:0;"></div>""", unsafe_allow_html=True)
    st.markdown("<h3 style='color:white; margin-bottom:20px; font-size:25px;'>Personal Information</h3>", unsafe_allow_html=True)

    name = st.text_input(
        "Display Name",
        value=(
            user.get("user_metadata", {}).get("name")
            or user.get("user_metadata", {}).get("full_name")
            or user.get("name")
            or user.get("full_name")
            or ""
        )
    )

    email = st.text_input("Email Address", value=user.get("email") or "", disabled=True)
    
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    if st.button("💾 Save Profile Changes"):
        try:
            user_id = user.get("id")
            if user_id:
                supabase.table("users").update({
                    "name": name
                }).eq("id", user_id).execute()
                st.success("Profile updated successfully ✅")
            else:
                st.warning("User ID not found in session.")
        except Exception as e:
            st.error(f"Failed to update profile: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    # About Card
    # st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("""<div style="margin-bottom:-5px; padding-bottom:0px;"><hr style="margin:0; padding:0;"></div>""", unsafe_allow_html=True)
    st.markdown("<h3 style='color:white; margin-bottom:15px; font-size:25px;'>System</h3>", unsafe_allow_html=True)

    st.markdown(f"""
        <div style="background: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.2);">
           <div style="color: #3b82f6; font-weight: 700; font-size: 20px;">{company_name}</div>
            <div style="color: rgba(255,255,255,0.5); font-size: 18px; margin-top:4px;">Secure Bid Management</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("##")
    st.caption(f"Environment: {APP_ENV}")
    st.caption(f"Access Level: {access_level} {'✅' if verified else '⚠️'}")
    # st.caption("Environment: production-v1.0")
    # st.caption("Access Level: Verified User")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    _, col1, _ = st.columns([4,4,4])

    with col1:
        if st.button("⬅ Back to Dashboard", key="back_btn"):
            st.switch_page("pages/dashboard.py")

    st.markdown("</div>", unsafe_allow_html=True)

# Footer
# st.markdown(f"<div style='text-align:center; margin-top:40px; color:rgba(255,255,255,0.2); font-size:11px;'>© 2026 Tenderflow Intelligence. All rights reserved.</div>", unsafe_allow_html=True)