import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import base64
import os

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="TenderFlow AI",
    layout="wide"
)

# -------------------------------------------------
# UTILS (BASE64 LOGO)
# -------------------------------------------------
def get_base64_of_bin_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# -------------------------------------------------
# GLOBAL STYLING
# -------------------------------------------------
st.markdown("""
<style>
    /* HIDE HEADER ANCHOR ICONS (-) */
    button[title="View header anchor"] {
        display: none !important;
    }
    .stHtmlHeader a , .stMarkdown a{
        display: none !important;
    }
    header { visibility: hidden; }
            
    .main {
        background-color: #0B0F14;
    }

    .block-container {
        padding: 3.5rem 1.5rem 1.2rem 1.5rem !important;
    }

    h1, h2, h3, h4 {
        color: #E5E7EB;
        font-weight: 600;
    }

    p, span, label {
        color: #9CA3AF;
        font-size: 0.85rem;
    }

    div[data-testid="metric-container"] {
        background-color: #111827;
        border: 1px solid #1F2937;
        padding: 10px;
        border-radius: 8px;
    }

    .js-plotly-plot {
        margin-top: -12px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
with st.sidebar:

    # ---- LOGO (BASE64, SAME AS LOGIN) ----
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
    logo_base64 = get_base64_of_bin_file(logo_path)

    if logo_base64:
        st.markdown(f"""
            <div style="text-align:center; margin-bottom:10px;">
                <img src="data:image/png;base64,{logo_base64}" width="140">
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("### TenderFlow")

    st.caption("Tender Intelligence Platform")
    st.markdown("<br>", unsafe_allow_html=True)

    # ---- NAVIGATION ----
    st.button("Overview", use_container_width=True)
    st.button("Active Tenders", use_container_width=True)
    st.button("Bid Intelligence", use_container_width=True)
    st.button("Compliance", use_container_width=True)
    st.button("Alerts", use_container_width=True)
    st.button("Settings", use_container_width=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ---- PROFILE POPOVER ----
    with st.popover("👤  Riddhi", use_container_width=True):
        st.markdown("**Riddhi Chauhan**")
        st.caption("Bid Manager")
        st.caption("KJ Somaiya Polytechnic")

        st.divider()

        st.button("⚙ Account Settings", use_container_width=True)
        st.button("🔄 Switch Organization", use_container_width=True)
        st.button("⏻ Logout", use_container_width=True)

# -------------------------------------------------
# HEADER
# -------------------------------------------------
header_left, header_right = st.columns([4, 1])

with header_left:
    st.markdown("## Overview")
    st.caption("Live snapshot of tender activity, risk, and AI readiness")

with header_right:
    st.markdown("<div style='margin-top:14px'></div>", unsafe_allow_html=True)
    st.button("➕ New Tender", use_container_width=True)

# -------------------------------------------------
# KPI STRIP
# -------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Active", "42")
k2.metric("Due < 7d", "9")
k3.metric("Avg Win %", "67%")
k4.metric("Prep Time", "3 days")
k5.metric("Compliance", "96%")

# -------------------------------------------------
# ACTIVE TENDERS TABLE
# -------------------------------------------------
st.markdown("### Active Tenders")

tenders = pd.DataFrame({
    "Tender": ["Mumbai Metro", "NH Infra", "Smart City", "Rail Electrification"],
    "Value (₹Cr)": [120, 85, 60, 45],
    "Deadline": ["4 days", "9 days", "14 days", "21 days"],
    "Compliance": ["92%", "98%", "95%", "97%"],
    "AI Status": ["⚠ Review", "✔ Verified", "✔ Verified", "✔ Verified"]
})

st.dataframe(tenders, use_container_width=True, hide_index=True)

# -------------------------------------------------
# PIPELINE + RISK
# -------------------------------------------------
left, right = st.columns(2)

pipeline = pd.DataFrame({
    "Stage": ["Identified", "Drafting", "Review", "Submitted"],
    "Count": [42, 18, 11, 7]
})

risk = pd.DataFrame({
    "Type": ["Missing Docs", "Legal", "Format"],
    "Count": [6, 3, 2]
})

with left:
    st.markdown("### Tender Pipeline")
    fig1 = px.bar(pipeline, x="Stage", y="Count", template="plotly_dark", height=220)
    fig1.update_layout(margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig1, use_container_width=True)

with right:
    st.markdown("### Risk Snapshot")
    fig2 = px.bar(risk, x="Type", y="Count", template="plotly_dark", height=220)
    fig2.update_layout(margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig2, use_container_width=True)

# -------------------------------------------------
# ALERTS + AI TRUST
# -------------------------------------------------
a1, a2 = st.columns([1.2, 1])

with a1:
    st.markdown("### Alerts")
    st.error("Mumbai Metro — Financial annexure missing")
    st.warning("NH Infra — Clause mismatch detected")

with a2:
    st.markdown("### AI Trust Status")
    st.success("✔ RAG Verification Active")
    st.success("✔ Local Embeddings Enabled")
    st.info("1 tender pending manual review")

# -------------------------------------------------
# FOOTER
# -------------------------------------------------
st.caption("TenderFlow AI • Secure • Compliant • Hallucination-Proof")
