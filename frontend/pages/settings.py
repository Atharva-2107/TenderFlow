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

# ---------------- AUTH GUARD ----------------
if not st.session_state.get("authenticated"):
    st.switch_page("pages/loginPage.py")
    st.stop()

if not st.session_state.get("onboarding_complete"):
    step = st.session_state.get("onboarding_step", 1)
    st.switch_page(f"pages/informationCollection_{step}.py")
    st.stop()

user = st.session_state.get("user", {})
company_id = st.session_state.get("company_id")

# ---------------- SUPABASE ----------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase environment variables not loaded")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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

.glass-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px;
    padding: 18px 22px;
}

.page-title {
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 6px;
}

.page-subtitle {
    font-size: 13px;
    color: rgba(255,255,255,0.70);
    margin-bottom: 18px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- UI ----------------
st.markdown("<div class='page-title'>⚙ Settings</div>", unsafe_allow_html=True)
st.markdown("<div class='page-subtitle'>Manage basic account information</div>", unsafe_allow_html=True)

left, right = st.columns([2, 1])

with left:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Edit Basic Information")

    name = st.text_input("Name", value=user.get("name") or user.get("full_name") or "")
    email = st.text_input("Email", value=user.get("email") or "", disabled=True)

    if st.button("💾 Save Changes"):
        try:
            # update user in DB (change table name based on your schema)
            # Example table: users, columns: id, name
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
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("About")

    st.write("**Tenderflow**")
    st.caption("Bid & Tender Management Dashboard")
    st.caption("Version: v1.0 (MVP)")

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    if st.button("⬅ Back to Dashboard"):
        st.switch_page("app.py")

    st.markdown("</div>", unsafe_allow_html=True)
