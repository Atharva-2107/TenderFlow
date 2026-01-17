import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit.components.v1 as components
import os
import time
from dotenv import load_dotenv
from supabase import create_client
from utils.auth import can_access
from utils.queries import get_tenders, get_bids, get_generated_tenders, get_pending_tenders, get_pending_bids
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

/* NOTIFICATION BANNER */
.notification-container {
    margin: 4px 0 12px 0;
    width: 100%;
}
.notification-card-unified {
    /* Sleek gradient background matching theme */
    background: linear-gradient(
        90deg,
        rgba(30, 41, 59, 0.7) 0%,
        rgba(15, 23, 42, 0.85) 100%
    );
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    
    /* Fine border for premium feel */
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-left: 3px solid #3b82f6; /* Accent line */
    
    /* Shape and Spacing */
    border-radius: 12px;
    padding: 10px 16px; /* Slightly tighter padding */
    width: 100%;
    
    /* Shadow */
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 
                0 2px 4px -1px rgba(0, 0, 0, 0.06);
    
    /* Flex layout to align items nicely */
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    animation: slideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideIn {
    from { opacity: 0; transform: translateY(-8px) scale(0.98); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

.notification-content {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
}

.notification-icon {
    font-size: 18px;
    background: rgba(59, 130, 246, 0.15);
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    color: #cbd5e1;
}

.notification-text-group {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.notification-title {
    color: #f1f5f9;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.01em;
}

.notification-subtitle {
    color: #94a3b8;
    font-size: 11px;
    font-weight: 500;
}
</style>
</style>
""", unsafe_allow_html=True)

# st.markdown(""" <hr> """, unsafe_allow_html=True)

# ============================================================
# PENDING ACTION HANDLER (Process Win/Lose BEFORE data fetch)
# ============================================================
if "pending_notification_action" in st.session_state:
    action_data = st.session_state.pop("pending_notification_action")
    project_name = action_data["project_name"]
    status = action_data["status"]
    
    # Update DB
    supabase.table("generated_tenders").update({"status": status}).eq("project_name", project_name).execute()
    
    # Clear cache to ensure fresh data
    get_generated_tenders.clear()
    
    # Show toast feedback
    st.toast(f"Marked '{project_name}' as {status.title()}!")

# ============================================================
# PENDING BID ACTION HANDLER (Process Win/Lose for Bid Strategies)
# ============================================================
if "pending_bid_action" in st.session_state:
    action_data = st.session_state.pop("pending_bid_action")
    bid_id = action_data["bid_id"]
    project_name = action_data["project_name"]
    won_status = action_data["won"]  # True for Won, False for Lost
    
    # Update DB - won column in bid_history_v2
    supabase.table("bid_history_v2").update({"won": won_status}).eq("id", bid_id).execute()
    
    # Show toast feedback
    result_text = "Won" if won_status else "Lost"
    st.toast(f"Marked bid '{project_name}' as {result_text}!")

# Data loading (NOW with fresh data if action was processed above)
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

st.markdown(""" <hr> """, unsafe_allow_html=True)

# NOTIFICATION AREA - Uses optimized direct query for pending tenders
pending_tenders = get_pending_tenders()  # Direct DB query, not cached for real-time updates

# Get unique pending tenders by project_name (show only one notification per project)
seen_projects = set()
unique_pending = []
for t in pending_tenders:
    proj = t.get("project_name", "Unnamed")
    if proj not in seen_projects:
        seen_projects.add(proj)
        unique_pending.append(t)

# ACTION HANDLER REVERTED: Using standard buttons to prevent session loss.
# (HTML links cause full page reload which kills st.session_state)

if unique_pending:
    st.markdown('<div class="notification-container">', unsafe_allow_html=True)
    for tender in unique_pending:
        tender_id = tender.get("id")
        project_name = tender.get("project_name", "Unnamed Tender")
        
        # Use columns for layout
        # Col 0: Text Card (Styled)
        # Col 1: Win Button
        # Col 2: Lose Button
        
        # We adjust layout to make buttons look "near" the text
        notif_cols = st.columns([0.7, 0.15, 0.15])
        
        with notif_cols[0]:
            st.markdown(f'''
                <div class="notification-card-unified" style="border-top-right-radius: 4px; border-bottom-right-radius: 4px; margin-right: -10px;">
                    <div class="notification-content">
                        <div class="notification-icon">🔔</div>
                        <div class="notification-text-group">
                            <div class="notification-title">{project_name}</div>
                            <div class="notification-subtitle">Decision Pending</div>
                        </div>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            
        with notif_cols[1]:
            # Align vertical
            st.markdown('<div style="height: 18px"></div>', unsafe_allow_html=True)
            if st.button("✅ Won", key=f"win_{tender_id}", type="primary", use_container_width=True):
                # Set pending action and rerun - action will be processed BEFORE data is fetched
                st.session_state["pending_notification_action"] = {
                    "project_name": project_name,
                    "status": "won"
                }
                st.rerun()
                
        with notif_cols[2]:
             st.markdown('<div style="height: 18px"></div>', unsafe_allow_html=True)
             if st.button("❌ Lost", key=f"lose_{tender_id}", use_container_width=True):
                st.session_state["pending_notification_action"] = {
                    "project_name": project_name,
                    "status": "lost"
                }
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# BID STRATEGY NOTIFICATIONS - Pending bid decisions
pending_bids = get_pending_bids()  # Direct DB query, not cached for real-time updates

# Get unique pending bids by project_name
seen_bid_projects = set()
unique_pending_bids = []
for bid in pending_bids:
    proj = bid.get("project_name", "Unnamed")
    if proj not in seen_bid_projects:
        seen_bid_projects.add(proj)
        unique_pending_bids.append(bid)

if unique_pending_bids:
    st.markdown('<div class="notification-container">', unsafe_allow_html=True)
    for bid in unique_pending_bids:
        bid_id = bid.get("id")
        project_name = bid.get("project_name", "Unnamed Bid")
        category = bid.get("category", "")
        
        bid_notif_cols = st.columns([0.7, 0.15, 0.15])
        
        with bid_notif_cols[0]:
            st.markdown(f'''
                <div class="notification-card-unified" style="border-left: 3px solid #10b981; border-top-right-radius: 4px; border-bottom-right-radius: 4px; margin-right: -10px;">
                    <div class="notification-content">
                        <div class="notification-icon" style="background: rgba(16, 185, 129, 0.15);">💰</div>
                        <div class="notification-text-group">
                            <div class="notification-title">{project_name}</div>
                            <div class="notification-subtitle">Bid Strategy • {category if category else "Uncategorized"}</div>
                        </div>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            
        with bid_notif_cols[1]:
            st.markdown('<div style="height: 18px"></div>', unsafe_allow_html=True)
            if st.button("✅ Won", key=f"bid_win_{bid_id}", type="primary", use_container_width=True):
                st.session_state["pending_bid_action"] = {
                    "bid_id": bid_id,
                    "project_name": project_name,
                    "won": True
                }
                st.rerun()
                
        with bid_notif_cols[2]:
            st.markdown('<div style="height: 18px"></div>', unsafe_allow_html=True)
            if st.button("❌ Lost", key=f"bid_lose_{bid_id}", use_container_width=True):
                st.session_state["pending_bid_action"] = {
                    "bid_id": bid_id,
                    "project_name": project_name,
                    "won": False
                }
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

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

#KPI dynamic - Now tracking actual won/lost status
unique_gen_tenders = len(set(g.get("project_name") for g in generated_tenders if g.get("project_name")))
total_bids = unique_gen_tenders

# Count won and lost by unique project names
won_projects = set(g.get("project_name") for g in generated_tenders if g.get("status") == "won" and g.get("project_name"))
lost_projects = set(g.get("project_name") for g in generated_tenders if g.get("status") == "lost" and g.get("project_name"))

won_bids = len(won_projects)
lost_bids = len(lost_projects)
total_value_won = 0  # Could be calculated if value field exists

# Calculate win/loss ratio as actual ratio string (e.g., "3:2")
win_ratio_display = f"{won_bids}:{lost_bids}"

capture_ratio = 0

kpi(c1, "Project Value Won", f"₹{total_value_won/1e7:.2f} Cr")
kpi(c2, "Win / Loss Ratio", win_ratio_display)
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

        # Map won status from the original data
        status_map = {g.get("id"): g.get("status") for g in generated_tenders}
        gen_df["won"] = gen_df["id"].apply(lambda x: 1 if status_map.get(x) == "won" else 0)
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
    
    # 1. Category Dropdown
    cat_options = ["Any", "Infrastructure", "IT & Technology", "Construction", 
                   "Supply & Procurement", "Healthcare", "Education", 
                   "Transport & Logistics", "Energy & Utilities"]
    
    selected_cat = st.selectbox("Filter Category", cat_options, label_visibility="collapsed")
    
    # 2. Filter Logic
    # Filter unique tenders by project_name to avoid duplicates (same logic as metrics)
    # Using the 'generated_tenders' list fetched earlier
    
    # Deduplicate first
    seen_projs = set()
    unique_tenders_list = []
    # Sort by created_at desc if possible
    # Assuming list is already somewhat ordered or we just take unique
    sorted_gen = sorted(generated_tenders, key=lambda x: x.get("created_at", ""), reverse=True)
    
    for t in sorted_gen:
        pname = t.get("project_name")
        if pname and pname not in seen_projs:
            seen_projs.add(pname)
            unique_tenders_list.append(t)
            
    # Apply Category Filter
    if selected_cat == "Any":
        # User requested: dont show tenders that have no category
        final_list = [t for t in unique_tenders_list if t.get("category") and t.get("category") not in ["None", ""]]
    else:
        final_list = [t for t in unique_tenders_list if t.get("category") == selected_cat]

    # 3. Display List
    if not final_list:
        st.info(f"No tenders found for category: {selected_cat}")
    else:
        # Build HTML rows
        # Format: "1. ProjectName (Category)" - No Value
        html_cat_rows = ""
        for i, item in enumerate(final_list[:8], 1): # Limit to 8
            name = item.get("project_name", "Unknown")
            cat = item.get("category")
            
            html_cat_rows += f"""
            <div style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 500; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 70%;" title="{name}"><b>{i}.</b> {name}</span>
                <span style="font-size: 12px; color: #a1a1aa; background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 6px; white-space: nowrap;">{cat}</span>
            </div>
            """

        components.html(
            f"""
            <style>
                /* Custom Scrollbar */
                ::-webkit-scrollbar {{
                    width: 6px;
                    height: 6px;
                }}
                ::-webkit-scrollbar-track {{
                    background: transparent;
                }}
                ::-webkit-scrollbar-thumb {{
                    background: rgba(255, 255, 255, 0.2);
                    border-radius: 3px;
                }}
                ::-webkit-scrollbar-thumb:hover {{
                    background: rgba(255, 255, 255, 0.3);
                }}
            </style>
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
                padding: 16px 20px;
                color: white;
                font-family: Inter, sans-serif;
                box-sizing: border-box; 
                height: 300px;
                overflow-y: auto;
                overflow-x: hidden;
            ">
                <div style="line-height: 1.6;">
                    {html_cat_rows}
                </div>
            </div>
            """,
            height=300,
            scrolling=False 
        )

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
    supabase.table("regulation_updates")
    .select("""
        title,
        tag,
        source,
        link,
        fetched_at
    """)
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
        tender_no = doc.get("title", None)
        doc_type = doc.get("tag", "Document")
        pdf_url = doc.get("link", None)
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

                    {"<div style='margin-top:8px; font-size:13px; color: rgba(255,255,255,0.9); line-height:1.4;'>🆔 Name: <span style='font-family: monospace; font-size: 13px; color: rgba(255,255,255,0.95);'>" + str(tender_no) + "</span></div>" if tender_no else ""}

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
