import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit.components.v1 as components
import os
from dotenv import load_dotenv
from supabase import create_client

# AUTH & ONBOARDING GUARD
if not st.session_state.get("authenticated"):
    st.switch_page("pages/loginPage.py")
    st.stop()

if not st.session_state.get("onboarding_complete"):
    step = st.session_state.get("onboarding_step", 1)
    st.switch_page(f"pages/informationCollection_{step}.py")
    st.stop()

user = st.session_state["user"]

# SUPABASE
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase environment variables not loaded")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# PAGE CONFIG
st.set_page_config(
    page_title="Tenderflow",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# SESSION STATE
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# GLOBAL CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: radial-gradient(circle at 20% 30%, #1a1c4b 0%, #0f111a 100%);
}

/* HEADER */
.header-title {
    font-size: 22px;
    font-weight: 600;
    color: #f8fafc;
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

/* KPI CARDS */
.kpi-card {
    background: linear-gradient(
        135deg,
        rgba(255,255,255,0.08),
        rgba(255,255,255,0.02)
    );
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px;
    padding: 18px 22px;
}

.kpi-title {
    font-size: 13px;
    color: #cbd5f5;
}

.kpi-value {
    font-size: 26px;
    font-weight: 700;
    color: #ffffff;
}

/* SECTION TITLES */
.section-title {
    color: #e5e7eb;
    font-size: 18px;
    font-weight: 600;
    margin: 22px 0 12px;
}
</style>
""", unsafe_allow_html=True)

# st.markdown(""" <hr> """, unsafe_allow_html=True)

# HEADER NAVIGATION
left, center, right = st.columns([3, 6, 3])

with left:
    st.image("frontend/assets/logo.png", width=180)

with center:
    header_cols = st.columns([3, 0.4, 0.4, 0.4, 0.4, 0.4])

    with header_cols[1]:
        if st.button("⊞", key="h_dash", help="Dashboard"):
            st.switch_page("app.py")

    with header_cols[2]:
        if st.button("⎘", key="h_gen", help="Tender Generation"):
            st.switch_page("pages/tenderGeneration.py")

    with header_cols[3]:
        if st.button("◈", key="h_anl", help="Tender Analysis"):
            st.switch_page("pages/tenderAnalyser.py")

    with header_cols[4]:
        if st.button("✦", key="h_bid", help="Bid Generation"):
            st.switch_page("pages/bidGeneration.py")

    with header_cols[5]:
        if st.button("⬈", key="h_risk", help="Risk Analysis"):
            st.switch_page("pages/riskAnalysis.py")

with right:
    r1, r2 = st.columns([1, 1])

    with r1:
        st.button("🔔", help="Notifications")

    with r2:
        with st.popover("⚙", help="Account"):
            if st.button("👤 Profile"):
                st.session_state.page = "Profile"
                st.experimental_rerun()
            if st.button("⚙ Settings"):
                st.session_state.page = "Settings"
                st.experimental_rerun()
            if st.button("⎋ Logout"):
                st.session_state.clear()
                st.experimental_rerun()

st.markdown("</div>", unsafe_allow_html=True)

# PAGE ROUTING
if st.session_state.page == "Profile":
    st.markdown("<div class='section-title'>Edit Profile</div>", unsafe_allow_html=True)
    st.text_input("Name")
    st.text_input("Email")
    st.button("Save Changes")
    st.stop()

if st.session_state.page == "Settings":
    st.markdown("<div class='section-title'>Settings</div>", unsafe_allow_html=True)
    st.toggle("Enable Notifications")
    st.toggle("Dark Mode")
    st.stop()

st.markdown(""" <hr> """, unsafe_allow_html=True)

# FILTERS 
st.markdown("<div class='section-title'>Filters</div>", unsafe_allow_html=True)

f1, f2, f3, f4, f5, f6 = st.columns(6)

with f1:
    st.date_input("Date Range")

with f2:
    st.multiselect("Tender Type", ["Open", "Limited", "Global"])

with f3:
    st.multiselect("Status", ["Open", "Won", "Lost", "In Progress"])

with f4:
    st.multiselect("Customers", ["Govt", "Private", "PSU"])

with f5:
    st.multiselect("Priority", ["High", "Medium", "Low"])

with f6:
    st.multiselect(
        "Business Line",
        ["Construction", "IT & Telecom", "Healthcare", "Energy"]
    )


# KPI SECTION
c1, c2, c3, c4 = st.columns(4)

def kpi(col, title, value):
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

kpi(c1, "Project Value Won", "₹2.45 Cr")
kpi(c2, "Win / Loss Ratio", "0.65")
kpi(c3, "Capture Ratio", "0.45")
kpi(c4, "Registered Opportunities", "185")

# BID ACTIVITY
st.markdown("<div class='section-title'>Bid Activity (All Time)</div>", unsafe_allow_html=True)

df = pd.DataFrame({
    "Month": ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
    "Bids Submitted": np.random.randint(80,160,12),
    "Bids Won": np.random.randint(40,120,12)
})

fig = px.line(df, x="Month", y=["Bids Submitted","Bids Won"], markers=True)
fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="white",
    legend_title_text=""
)

st.plotly_chart(fig, use_container_width=True)

# INSIGHTS
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='section-title'>Tenders by Category</div>", unsafe_allow_html=True)
    pie = px.pie(
        names=["Construction", "IT & Telecom", "Healthcare", "Energy"],
        values=[40, 27, 18, 15],
        hole=0.6
    )
    pie.update_layout(
        height=320,
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="white"
    )
    st.plotly_chart(pie, use_container_width=True)

with col2:
    components.html(
        """
        <div style="
            background: linear-gradient(
                135deg,
                rgba(255,255,255,0.08),
                rgba(255,255,255,0.02)
            );
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 16px;
            padding: 22px;
            max-width: 520px;
            margin: auto;
            color: white;
            font-family: Inter, sans-serif;
        ">
            <h4 style="margin-bottom: 16px;">Top 5 Highest Bids</h4>
            <div style="line-height: 2.2; font-size: 15px;">
                <b>1.</b> Metro Rail Project — ₹12.0 Cr<br>
                <b>2.</b> Hospital Development — ₹9.5 Cr<br>
                <b>3.</b> Telecom Infrastructure — ₹7.8 Cr<br>
                <b>4.</b> Renewable Energy Plant — ₹6.5 Cr<br>
                <b>5.</b> Highway Expansion — ₹5.0 Cr
            </div>
        </div>
        """,
        height=300
    )
