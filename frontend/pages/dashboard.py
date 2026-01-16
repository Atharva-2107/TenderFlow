import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit.components.v1 as components
import os
from dotenv import load_dotenv
from supabase import create_client
from utils.auth import can_access
from utils.queries import get_tenders, get_bids, get_generated_tenders
import base64
from pathlib import Path


# ROLE_PERMISSIONS = {
#     "Bid Manager": {
#         "tender_generation": True,
#         "tender_analysis": True,
#         "bid_generation": True,
#         "risk_analysis": True
#     },
#     "Risk Reviewer": {
#         "tender_generation": False,
#         "tender_analysis": True,
#         "bid_generation": False,
#         "risk_analysis": True
#     },
#     "Executive": {
#         "tender_generation": False,
#         "tender_analysis": False,
#         "bid_generation": False,
#         "risk_analysis": False
#     },
#     "Procurement Officer": {
#         "tender_generation": True,
#         "tender_analysis": True,
#         "bid_generation": True,
#         "risk_analysis": True
#     }
# }

# def can_access(feature: str) -> bool:
#     role = st.session_state.get("user_role")
#     return ROLE_PERMISSIONS.get(role, {}).get(feature, False)


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

def get_base64_of_bin_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# GLOBAL CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

header, footer { visibility:hidden; }
              
div.block-container {
    padding-top: 0.8rem !important; 
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
    padding: 12px 12px;
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

#Data loading
tenders = get_tenders()
# bids = get_bids() # REMOVED: User requested to ignore bid_history
generated_tenders = get_generated_tenders()

# HEADER NAVIGATION
left, center, right = st.columns([3, 6, 3])

with left:
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
    logo = get_base64_of_bin_file(logo_path)

    if logo:
        st.markdown(f"""
            <div style="display:flex; align-items:center;">
                <img src="data:image/png;base64,{logo}" width="180">
            </div>
        """, unsafe_allow_html=True)

with center:
    header_cols = st.columns([3, 0.4, 0.4, 0.4, 0.4, 0.4])

    with header_cols[1]:
        if st.button("⊞", key="h_dash", help="Dashboard"):
            st.switch_page("app.py")

    with header_cols[2]:
        if can_access("tender_generation"):
            if st.button("⎘", key="h_gen", help="Tender Generation"):
                st.switch_page("pages/tenderGeneration.py")
        else:
            st.button("⎘", key="h_gen_disabled", disabled=True, help="Access restricted")


    with header_cols[3]:
        if can_access("tender_analysis"):
            if st.button("◈", key="h_anl", help="Tender Analysis"):
                st.switch_page("pages/tenderAnalyser.py")
        else:
            st.button("◈", key="h_anl_disabled", disabled=True)

    with header_cols[4]:
        if can_access("bid_generation"):
            if st.button("✦", key="h_bid", help="Bid Generation"):
                st.switch_page("pages/bidGeneration.py")
        else:
            st.button("✦", key="h_bid_disabled", disabled=True)

    with header_cols[5]:
        if can_access("risk_analysis"):
            if st.button("⬈", key="h_risk", help="Risk Analysis"):
                st.switch_page("pages/riskAnalysis.py")
        else:
            st.button("⬈", key="h_risk_disabled", disabled=True)

with right:
    r1, r2 = st.columns([5, 5])

    with r1:
        st.button("🔔", help="Notifications")

    with r2:
        with st.popover("⚙", help="Account"):
            if st.button("👤 Profile"):
                st.switch_page("pages/profile.py")

            if st.button("⚙ Settings"):
                st.switch_page("pages/settings.py")

            if st.button("⎋ Logout"):
                st.session_state.clear()
                st.switch_page("pages/loginPage.py")


# st.markdown("</div>", unsafe_allow_html=True)

# PAGE ROUTING
# if st.session_state.page == "Profile":
#     st.markdown("<div class='section-title'>Edit Profile</div>", unsafe_allow_html=True)
#     st.text_input("Name")
#     st.text_input("Email")
#     st.button("Save Changes")
#     st.stop()

# if st.session_state.page == "Settings":
#     st.markdown("<div class='section-title'>Settings</div>", unsafe_allow_html=True)
#     st.toggle("Enable Notifications")
#     st.toggle("Dark Mode")
#     st.stop()

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

#KPI dynamic
# ONLY GENERATED TENDERS NOW
unique_gen_tenders = len(set(g.get("project_name") for g in generated_tenders if g.get("project_name")))
total_bids = unique_gen_tenders
# Generated tenders don't have 'won' status or value yet, so these are 0 for now
won_bids = 0 
total_value_won = 0

win_ratio = 0
capture_ratio = 0

kpi(c1, "Project Value Won", f"₹{total_value_won/1e7:.2f} Cr")
kpi(c2, "Win / Loss Ratio", win_ratio)
kpi(c3, "Capture Ratio", capture_ratio)
kpi(c4, "Registered Opportunities", len(tenders))

st.markdown("<div class='section-title'>Bid Activity (All Time)</div>", unsafe_allow_html=True)

# Process Generated Tenders (Treat as Bids Submitted)
gen_df = pd.DataFrame(generated_tenders)

if gen_df.empty:
    st.info("No bid activity available")
    # Stop earlier if purely empty
else:
    if "created_at" in gen_df.columns:
        gen_df["created_at"] = pd.to_datetime(gen_df["created_at"], errors="coerce")
        gen_df = gen_df.dropna(subset=["created_at"])
        
        # UNIQUE TENDER LOGIC: Drop duplicates by project_name to count 1 tender per project
        if "project_name" in gen_df.columns:
            gen_df = gen_df.sort_values("created_at") # Ensure we keep latest if duplicates
            gen_df = gen_df.drop_duplicates(subset=["project_name"], keep="last")

        gen_df["won"] = 0 # Generated but not strictly "won" yet
        combined_df = gen_df[["created_at", "won", "id"]] # Select relevant cols
    else:
        combined_df = pd.DataFrame()

    if combined_df.empty:
        st.info("No valid activity data available")
        st.stop()

    combined_df["Month"] = combined_df["created_at"].dt.to_period("M").dt.to_timestamp()

    activity_df = (
        combined_df.groupby("Month", as_index=False)
        .agg(
            Bids_Submitted=("id", "count"),
            Bids_Won=("won", "sum")
        )
        .sort_values("Month")
    )

    # ✅ Another safety check
    if activity_df.empty:
        st.info("No bid activity available")
    else:
        # VISUAL FIX: If only 1 data point, add a preceding 0 point to show a line from 0
        if len(activity_df) == 1:
            first_month = activity_df.iloc[0]["Month"]
            prev_month = first_month - pd.DateOffset(months=1)
            zero_row = pd.DataFrame({
                "Month": [prev_month],
                "Bids_Submitted": [0],
                "Bids_Won": [0]
            })
            activity_df = pd.concat([zero_row, activity_df], ignore_index=True)

        activity_df["Month_Label"] = activity_df["Month"].dt.strftime("%b %Y")

        fig = px.line(
            activity_df,
            x="Month_Label",
            y=["Bids_Submitted", "Bids_Won"],
            markers=True
        )

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
    st.info("Category insights will be enabled once structured fields are finalized.")
    # st.markdown("<div class='section-title'>Tenders by Category</div>", unsafe_allow_html=True)
    # pie = px.pie(
    #     st.info("Category insights will be enabled once structured fields are finalized.")
    #     # names=["Construction", "IT & Telecom", "Healthcare", "Energy"],
    #     # values=[40, 27, 18, 15],
    #     # hole=0.6
    # )
    # pie.update_layout(
    #     height=320,
    #     margin=dict(t=20, b=20, l=20, r=20),
    #     legend=dict(
    #         orientation="h",
    #         yanchor="top",
    #         y=-0.15,
    #         xanchor="center",
    #         x=0.5
    #     ),
    #     paper_bgcolor="rgba(0,0,0,0)",
    #     font_color="white"
    # )
    # st.plotly_chart(pie, use_container_width=True)

with col2:
    st.markdown("<div class='section-title'>Top 5 Highest Bids</div>", unsafe_allow_html=True)

    top_bids = [] 
    # sorted(
    #     [b for b in bids if b.get("final_bid_amount") and b.get("tender_id")],
    #     key=lambda x: x["final_bid_amount"],
    #     reverse=True
    # )[:5]

    if not top_bids:
        st.info("No bids available")
    else:
        html_rows = ""
        for i, bid in enumerate(top_bids, 1):
            html_rows += f"""
            <div style="margin-bottom: 10px;">
                <b>{i}.</b> Tender ID {bid['tender_id']} — ₹{bid['final_bid_amount']/1e7:.2f} Cr
            </div>
            """

        components.html(
            f"""
            <div style="
                width: 100%;
                background: linear-gradient(
                    135deg,
                    rgba(255,255,255,0.08),
                    rgba(255,255,255,0.02)
                );
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 16px;
                padding: 22px;
                color: white;
                font-family: Inter, sans-serif;
            ">
                <div style="line-height: 1.8; font-size: 15px;">
                    {html_rows}
                </div>
            </div>
            """,
            height=260
        )


# REGULATORY & BID DOCUMENTATION (Scrollable Container)
st.markdown("<div class='section-title'>Regulatory & Bid Documentation Updates</div>", unsafe_allow_html=True)

try:
    response = (
        supabase.table("tender_documents")
        .select("source, tender_no, document_type, structured_data, pdf_url, fetched_at")
        .order("fetched_at", desc=True)
        .limit(15)
        .execute()
    )
    updates = response.data or []
except Exception:
    updates = []

if not updates:
    st.info("No recent regulatory or bid documentation updates available.")
else:
    scroll_html = """
    <div style="
        font-family: 'Inter', 'Manrope', 'Segoe UI', Arial, sans-serif;
        background: linear-gradient(
            135deg,
            rgba(255,255,255,0.08),
            rgba(255,255,255,0.02)
        );
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 16px;
        padding: 16px;
        height: 380px;
        overflow-y: auto;
    ">
    """

    for doc in updates:
        source = doc.get("source", "Unknown Source")
        tender_no = doc.get("tender_no", None)
        doc_type = doc.get("document_type", "Document")
        pdf_url = doc.get("pdf_url", None)
        fetched_at = doc.get("fetched_at", "")

        structured = doc.get("structured_data") or {}
        deadline = structured.get("submission_deadline", None)

        fetched_label = fetched_at[:19].replace("T", " ") if fetched_at else "N/A"

        scroll_html += f"""
        <div style="
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 12px;
        ">
            <div style="display: flex; justify-content: space-between; gap: 16px;">

                <div style="flex: 1; min-width: 0;">
                    <div style="
                        font-size: 16px;
                        font-weight: 700;
                        color: white;
                        margin-bottom: 6px;
                        line-height: 1.3;
                    ">
                        {doc_type}
                    </div>

                    <div style="
                        font-size: 13px;
                        color: rgba(255,255,255,0.78);
                        line-height: 1.4;
                    ">
                        Source: <span style="font-weight: 600; color: rgba(255,255,255,0.92);">{source}</span>
                    </div>

                    {"<div style='margin-top:8px; font-size:13px; color: rgba(255,255,255,0.9); line-height:1.4;'>🆔 Tender No: <span style='font-family: monospace; font-size: 13px; color: rgba(255,255,255,0.95);'>" + str(tender_no) + "</span></div>" if tender_no else ""}

                    {"<div style='margin-top:6px; font-size:13px; color: rgba(255,255,255,0.92); line-height:1.4;'>⏳ Deadline: <span style='font-weight:700;'>" + str(deadline) + "</span></div>" if deadline else ""}

                    <div style="
                        margin-top: 10px;
                        font-size: 12px;
                        color: rgba(255,255,255,0.55);
                        line-height: 1.4;
                    ">
                        🕒 Updated: {fetched_label}
                    </div>
                </div>

                <div style="min-width: 120px; display: flex; align-items: center;">
                    {
                        f'''
                        <a href="{pdf_url}" target="_blank" style="
                            display: inline-block;
                            width: 100%;
                            text-align: center;
                            padding: 10px 12px;
                            border-radius: 12px;
                            background: rgba(255,255,255,0.12);
                            border: 1px solid rgba(255,255,255,0.20);
                            color: white;
                            text-decoration: none;
                            font-weight: 700;
                            font-size: 13px;
                            letter-spacing: 0.2px;
                        ">
                            📄 View PDF
                        </a>
                        ''' if pdf_url else
                        '''
                        <div style="
                            width: 100%;
                            text-align: center;
                            padding: 10px 12px;
                            border-radius: 12px;
                            background: rgba(255,255,255,0.05);
                            border: 1px solid rgba(255,255,255,0.10);
                            color: rgba(255,255,255,0.55);
                            font-weight: 700;
                            font-size: 13px;
                            letter-spacing: 0.2px;
                        ">
                            No PDF
                        </div>
                        '''
                    }
                </div>

            </div>
        </div>
        """

    scroll_html += "</div>"

    components.html(scroll_html, height=400)
