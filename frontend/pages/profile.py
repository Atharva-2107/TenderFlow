import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from supabase import create_client
import base64
import os
import re
import time
from pathlib import Path
from datetime import date

def get_base64_of_bin_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# SETTINGS & AUTH
load_dotenv()
st.set_page_config(page_title="Profile • TenderFlow", page_icon="👤", layout="wide")

if not st.session_state.get("authenticated"):
    st.switch_page("pages/loginPage.py")
    st.stop()

if not st.session_state.get("onboarding_complete"):
    step = st.session_state.get("onboarding_step", 1)
    st.switch_page(f"pages/informationCollection_{step}.py")
    st.stop()

# SESSION DATA
user_obj = st.session_state.get("user")
user_role = st.session_state.get("user_role", "Unknown")
company_id = st.session_state.get("company_id")

# SUPABASE
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase environment variables not loaded")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Authenticate with session token
sb_session = st.session_state.get("sb_session")
if sb_session:
    supabase.postgrest.auth(sb_session.access_token)

# USER SAFE CONVERSION
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

user_id = user.get("id") or (user_obj.id if hasattr(user_obj, "id") else None)
user_email = user.get("email", "Not available")

# FETCH ALL COMPANY & PROFILE DATA
company_name = "Not linked"
invite_code = None
company_info = {}     # from company_information table (step 1)
compliance_info = {}  # from business_compliance table (step 2)
financial_info = {}   # from financials table (step 3)
experience_records = []  # from experience_records table (step 4)

if company_id:
    try:
        res = supabase.table("companies").select("name, invite_code").eq("id", company_id).single().execute()
        if res.data:
            company_name = res.data.get("name", "Not linked")
            invite_code = res.data.get("invite_code")
    except Exception:
        pass

if user_id:
    try:
        r = supabase.table("company_information").select("*").eq("id", user_id).maybe_single().execute()
        if r and r.data:
            company_info = r.data
            if not company_name or company_name == "Not linked":
                company_name = company_info.get("company_name", company_name)
    except Exception:
        pass

    try:
        r = supabase.table("business_compliance").select("*").eq("user_id", user_id).maybe_single().execute()
        if r and r.data:
            compliance_info = r.data
    except Exception:
        pass

    try:
        r = supabase.table("financials").select("*").eq("user_id", user_id).maybe_single().execute()
        if r and r.data:
            financial_info = r.data
    except Exception:
        pass

    try:
        r = supabase.table("experience_records").select("project_name, client_name, client_type, work_category, contract_value, completion_status, completion_date").eq("user_id", user_id).execute()
        if r and r.data:
            experience_records = r.data
    except Exception:
        pass

# PROFILE COMPLETION
has_company_info = bool(company_info.get("company_name"))
has_compliance = bool(compliance_info.get("gst_number"))
has_financials = bool(financial_info.get("avg_annual_turnover"))
has_experience = len(experience_records) > 0

completion_checks = {
    "Account": bool(user_email and user_email != "Not available"),
    "Role": bool(user_role and user_role != "Unknown"),
    "Company": bool(company_name and company_name != "Not linked"),
    "Compliance": has_compliance,
    "Financials": has_financials,
    "Experience": has_experience,
}
completion_percent = int((sum(completion_checks.values()) / len(completion_checks)) * 100)

# CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.stApp {
    background: radial-gradient(circle at 20% 30%, #1a1c4b 0%, #0f111a 100%) !important;
    color: white;
}

header, footer { visibility: hidden; }
.block-container { padding-top: 0.5rem !important; max-width: 1200px; margin: auto; }

/* Glass card */
.glass-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 18px;
    padding: 22px 26px;
    margin-bottom: 18px;
    backdrop-filter: blur(20px);
}

.card-title {
    color: #a855f7;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.info-row {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    margin-bottom: 14px;
}

.info-label {
    color: rgba(255,255,255,0.45);
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    min-width: 150px;
}

.info-value {
    color: rgba(255,255,255,0.92);
    font-size: 14px;
    font-weight: 500;
    word-break: break-word;
}

.chip {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 100px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

.chip-role {
    background: rgba(168,85,247,0.18);
    border: 1px solid rgba(168,85,247,0.4);
    color: #d8b4fe;
}

.chip-done {
    background: rgba(34,197,94,0.15);
    border: 1px solid rgba(34,197,94,0.35);
    color: #86efac;
}

.chip-todo {
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.3);
    color: #fca5a5;
}

.divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.07);
    margin: 14px 0;
}

.exp-row {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 10px;
}

.exp-proj { color: white; font-size: 14px; font-weight: 600; }
.exp-meta { color: rgba(255,255,255,0.5); font-size: 12px; margin-top: 3px; }

/* Progress bar override */
div[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #7c3aed, #a855f7) !important;
    border-radius: 999px !important;
}

/* Streamlit button overrides */
div.stButton > button {
    background: rgba(168,85,247,0.15) !important;
    border: 1px solid rgba(168,85,247,0.4) !important;
    color: #d8b4fe !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}

div.stButton > button:hover {
    background: rgba(168,85,247,0.3) !important;
}

/* Form inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: white !important;
    border-radius: 10px !important;
}

div[data-testid="stForm"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 16px !important;
    padding: 20px !important;
}
</style>
""", unsafe_allow_html=True)

# LOGO ROW
logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
logo = get_base64_of_bin_file(logo_path)

header_c1, header_c2 = st.columns([2, 1])
with header_c1:
    if logo:
        st.markdown(f'<img src="data:image/png;base64,{logo}" width="170" style="margin-bottom:4px">', unsafe_allow_html=True)

with header_c2:
    st.write("")
    if st.button("⬅ Back to Dashboard", use_container_width=True):
        st.switch_page("app.py")

# PAGE TITLE
st.markdown(f"""
<div style="margin-bottom:20px;">
    <h1 style="color:white;font-size:28px;font-weight:800;margin:0">👤 My Profile</h1>
    <p style="color:rgba(255,255,255,0.5);margin:4px 0 0 0;font-size:14px">Account identity, organization profile & past performance</p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# LAYOUT: LEFT COLUMN (Account + Company Info + Compliance + Experience)
# RIGHT COLUMN (Completion + Financials + Edit Form)
# ═══════════════════════════════════════════════════════════════
left_col, right_col = st.columns([1.6, 1], gap="large")

with left_col:

    # ── ACCOUNT INFO ──────────────────────────────────────────
    st.markdown("""<div class="glass-card">
        <div class="card-title">🔐 Account</div>""", unsafe_allow_html=True)

    st.markdown(f"""
        <div class="info-row">
            <div class="info-label">Email</div>
            <div class="info-value">{user_email}</div>
        </div>
        <div class="info-row">
            <div class="info-label">System Role</div>
            <div class="info-value"><span class="chip chip-role">{user_role}</span></div>
        </div>
        <div class="info-row">
            <div class="info-label">Organization</div>
            <div class="info-value">{company_name}</div>
        </div>""", unsafe_allow_html=True)

    # Invite code
    if invite_code:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="info-label" style="margin-bottom:8px;">Workspace Invite Code</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([2.5, 1])
        with c1:
            st.code(invite_code, language="text")
        with c2:
            components.html(f"""
            <button onclick="navigator.clipboard.writeText('{invite_code}')"
            style="width:100%;height:38px;cursor:pointer;background:rgba(168,85,247,0.2);
            border:1px solid rgba(168,85,247,0.4);border-radius:8px;color:#d8b4fe;
            font-weight:700;font-size:12px;font-family:Plus Jakarta Sans,sans-serif;">
            📋 Copy
            </button>""", height=48)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── COMPANY INFORMATION ───────────────────────────────────
    st.markdown("""<div class="glass-card">
        <div class="card-title">🏢 Company Information</div>""", unsafe_allow_html=True)

    if company_info:
        def row(label, val):
            v = val or "—"
            return f'<div class="info-row"><div class="info-label">{label}</div><div class="info-value">{v}</div></div>'

        st.markdown(
            row("Company Name", company_info.get("company_name")) +
            row("Org Type", company_info.get("org_type")) +
            row("Incorp. Date", str(company_info.get("incorp_date", "")) or None) +
            row("Contact Email", company_info.get("email")) +
            row("Phone", company_info.get("phone_number")) +
            row("Designation", company_info.get("designation")) +
            row("Reg. Address", company_info.get("reg_address")) +
            row("Office Address", company_info.get("office_address")) +
            row("Authorized Signatory", company_info.get("authorized_signatory")),
            unsafe_allow_html=True
        )
    else:
        st.markdown('<p style="color:rgba(255,255,255,0.35);font-size:13px;">No company information found. Complete Step 1 of onboarding.</p>', unsafe_allow_html=True)
        if st.button("📝 Fill Company Info (Step 1)", key="go_step1"):
            st.session_state["onboarding_complete"] = False
            st.switch_page("pages/informationCollection_1.py")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── COMPLIANCE INFO ───────────────────────────────────────
    st.markdown("""<div class="glass-card">
        <div class="card-title">⚖️ Legal & Compliance</div>""", unsafe_allow_html=True)

    if compliance_info:
        # Mask sensitive data
        def mask(val, show=4):
            if not val:
                return "—"
            return ("*" * max(0, len(str(val)) - show)) + str(val)[-show:]

        gst = compliance_info.get("gst_number", "")
        gst_display = f"{gst[:2]}****{gst[-4:]}" if gst and len(gst) > 6 else (gst or "—")

        st.markdown(f"""
        <div class="info-row"><div class="info-label">GST Number</div><div class="info-value">{gst_display}</div></div>
        <div class="info-row"><div class="info-label">PAN Number</div><div class="info-value">{mask(compliance_info.get('pan_number'))}</div></div>
        <div class="info-row"><div class="info-label">Bank Account</div><div class="info-value">{mask(compliance_info.get('bank_account_number'))}</div></div>
        <div class="info-row"><div class="info-label">IFSC Code</div><div class="info-value">{compliance_info.get('ifsc_code', '—')}</div></div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:rgba(255,255,255,0.35);font-size:13px;">No compliance data found. Complete Step 2 of onboarding.</p>', unsafe_allow_html=True)
        if st.button("📝 Fill Compliance Info (Step 2)", key="go_step2"):
            st.session_state["onboarding_complete"] = False
            st.switch_page("pages/informationCollection_2.py")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── EXPERIENCE RECORDS ────────────────────────────────────
    st.markdown("""<div class="glass-card">
        <div class="card-title">🏗️ Past Experience</div>""", unsafe_allow_html=True)

    if experience_records:
        for exp in experience_records:
            proj = exp.get("project_name", "Unnamed Project")
            client = exp.get("client_name", "")
            ctype = exp.get("client_type", "")
            cat = exp.get("work_category", "")
            val = exp.get("contract_value", "")
            status = exp.get("completion_status", "")
            status_color = "#86efac" if status == "Completed" else "#fcd34d"
            st.markdown(f"""
            <div class="exp-row">
                <div class="exp-proj">{proj} <span style="color:{status_color};font-size:11px;font-weight:600;">● {status}</span></div>
                <div class="exp-meta">{client} ({ctype}) · {cat} · ₹{val}</div>
            </div>""", unsafe_allow_html=True)
        if st.button("➕ Add More Experience", key="go_step4"):
            st.session_state["onboarding_complete"] = False
            st.switch_page("pages/informationCollection_4.py")
    else:
        st.markdown('<p style="color:rgba(255,255,255,0.35);font-size:13px;">No experience records found. Complete Step 4 of onboarding.</p>', unsafe_allow_html=True)
        if st.button("📝 Add Experience (Step 4)", key="go_step4_empty"):
            st.session_state["onboarding_complete"] = False
            st.switch_page("pages/informationCollection_4.py")

    st.markdown("</div>", unsafe_allow_html=True)


with right_col:

    # ── PROFILE COMPLETION ────────────────────────────────────
    st.markdown("""<div class="glass-card">
        <div class="card-title">📊 Profile Completion</div>""", unsafe_allow_html=True)

    color = "#86efac" if completion_percent >= 80 else "#fcd34d" if completion_percent >= 50 else "#f87171"
    st.markdown(f"""
    <div style="font-size:38px;font-weight:800;color:{color};line-height:1;">{completion_percent}%</div>
    <div style="color:rgba(255,255,255,0.4);font-size:12px;margin-bottom:10px;">Profile completeness</div>
    """, unsafe_allow_html=True)
    st.progress(completion_percent / 100)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    for check_name, check_val in completion_checks.items():
        status_chip = f'<span class="chip chip-done">✓</span>' if check_val else f'<span class="chip chip-todo">✗</span>'
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <span style="color:rgba(255,255,255,0.7);font-size:13px;">{check_name}</span>
            {status_chip}
        </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── FINANCIAL INFO ────────────────────────────────────────
    st.markdown("""<div class="glass-card">
        <div class="card-title">💰 Financial Overview</div>""", unsafe_allow_html=True)

    if financial_info:
        at = financial_info.get("avg_annual_turnover", "—")
        fy = financial_info.get("fy_wise_turnover", "—")
        st.markdown(f"""
        <div class="info-row"><div class="info-label">Avg Annual Turnover</div></div>
        <div style="color:white;font-size:18px;font-weight:700;margin-bottom:12px;">₹{at}</div>
        <div class="info-label" style="margin-bottom:6px;">FY-wise Breakdown</div>
        <div style="color:rgba(255,255,255,0.7);font-size:13px;line-height:1.7;">{fy.replace(',','<br>') if fy else '—'}</div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:rgba(255,255,255,0.35);font-size:13px;">No financial data. Complete Step 3 of onboarding.</p>', unsafe_allow_html=True)
        if st.button("📝 Fill Financial Info (Step 3)", key="go_step3"):
            st.session_state["onboarding_complete"] = False
            st.switch_page("pages/informationCollection_3.py")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── QUICK EDIT COMPANY INFO ───────────────────────────────
    with st.expander("✏️ Edit Company Info", expanded=False):
        with st.form("edit_company_form"):
            st.markdown('<div style="color:rgba(255,255,255,0.7);font-size:12px;margin-bottom:12px;">Update your company information directly from this page.</div>', unsafe_allow_html=True)

            new_company_name = st.text_input("Company Name", value=company_info.get("company_name", ""), placeholder="Official registered name")
            new_email = st.text_input("Contact Email", value=company_info.get("email", ""), placeholder="name@company.com")
            new_phone = st.text_input("Contact Phone", value=company_info.get("phone_number", ""), placeholder="+91XXXXXXXXXX")
            new_signatory = st.text_input("Authorized Signatory", value=company_info.get("authorized_signatory", ""), placeholder="Full legal name")
            new_reg_addr = st.text_area("Registered Address", value=company_info.get("reg_address", ""), height=80)

            submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)

            if submitted:
                if not user_id:
                    st.error("User ID not found. Please log in again.")
                else:
                    try:
                        update_data = {
                            "id": user_id,
                            "company_name": new_company_name,
                            "email": new_email,
                            "phone_number": new_phone,
                            "authorized_signatory": new_signatory,
                            "reg_address": new_reg_addr,
                        }
                        if company_id:
                            update_data["company_id"] = company_id
                        supabase.table("company_information").upsert(update_data, on_conflict="id").execute()
                        st.success("✅ Company information updated!")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save: {e}")
