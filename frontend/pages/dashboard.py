# import streamlit as st
# import pandas as pd
# import plotly.express as px
# from pathlib import Path
# import os
# from supabase import create_client
# from components.navbar import render_navbar

# if not st.session_state.get("authenticated"):
#     st.switch_page("pages/loginPage.py")
#     st.stop()

# if not st.session_state.get("onboarding_complete"):
#     step = st.session_state.get("onboarding_step", 1)
#     st.switch_page(f"pages/informationCollection_{step}.py")
#     st.stop()

# user = st.session_state["user"]

# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")
# if not SUPABASE_URL or not SUPABASE_KEY:
#     st.error("Supabase environment variables not loaded")
#     st.stop()

# supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# #auth_and_onboarding_guard(supabase)


# # PAGE CONFIG
# st.set_page_config(
#     page_title="TenderFlow AI",
#     layout="wide"
# )


# # CALL REUSABLE NAVBAR
# render_navbar()

# # GLOBAL STYLING
# st.markdown("""
# <style>
#     /* HIDE HEADER ANCHOR ICONS (-) */
#     button[title="View header anchor"] {
#         display: none !important;
#     }
#     .stHtmlHeader a , .stMarkdown a{
#         display: none !important;
#     }
    
#     .main {
#         background-color: #0B0F14;
#     }

#     /* Padding adjustment is handled inside navbar.py's CSS, 
#        but we keep local dashboard styles here */
#     h1, h2, h3, h4 {
#         color: #E5E7EB;
#         font-weight: 600;
#     }

#     p, span, label {
#         color: #9CA3AF;
#         font-size: 0.85rem;
#     }

#     div[data-testid="metric-container"] {
#         background-color: #111827;
#         border: 1px solid #1F2937;
#         padding: 10px;
#         border-radius: 8px;
#     }

#     .js-plotly-plot {
#         margin-top: -12px;
#     }
# </style>
# """, unsafe_allow_html=True)


# # SIDEBAR
# with st.sidebar:
#     # Space for the fixed navbar
#     st.markdown("<br><br>", unsafe_allow_html=True)
    
#     st.caption("Tender Intelligence Platform")
#     st.markdown("<br>", unsafe_allow_html=True)

#     # NAVIGATION 
#     st.button("Overview", use_container_width=True)
#     st.button("Active Tenders", use_container_width=True)
#     st.button("Bid Intelligence", use_container_width=True)
#     st.button("Compliance", use_container_width=True)
#     st.button("Alerts", use_container_width=True)
#     st.button("Settings", use_container_width=True)

#     st.markdown("<br><br>", unsafe_allow_html=True)

#     # PROFILE POPOVER
#     with st.popover("👤   Riddhi", use_container_width=True):
#         st.markdown("**Riddhi Chauhan**")
#         st.caption("Bid Manager")
#         st.caption("KJ Somaiya Polytechnic")
#         st.divider()
#         st.button("⚙ Account Settings", use_container_width=True)
#         st.button("🔄 Switch Organization", use_container_width=True)
#         st.button("⏻ Logout", use_container_width=True)


# # DASHBOARD MAIN CONTENT
# header_left, header_right = st.columns([4, 1])

# with header_left:
#     st.markdown("## Overview")
#     st.caption("Live snapshot of tender activity, risk, and AI readiness")

# with header_right:
#     st.markdown("<div style='margin-top:14px'></div>", unsafe_allow_html=True)
#     st.button("➕ New Tender", use_container_width=True)

# #  KPI STRIP 
# k1, k2, k3, k4, k5 = st.columns(5)
# k1.metric("Active", "42")
# k2.metric("Due < 7d", "9")
# k3.metric("Avg Win %", "67%")
# k4.metric("Prep Time", "3 days")
# k5.metric("Compliance", "96%")

# #ACTIVE TENDERS TABLE
# st.markdown("### Active Tenders")
# tenders = pd.DataFrame({
#     "Tender": ["Mumbai Metro", "NH Infra", "Smart City", "Rail Electrification"],
#     "Value (₹Cr)": [120, 85, 60, 45],
#     "Deadline": ["4 days", "9 days", "14 days", "21 days"],
#     "Compliance": ["92%", "98%", "95%", "97%"],
#     "AI Status": ["⚠ Review", "✔ Verified", "✔ Verified", "✔ Verified"]
# })
# st.dataframe(tenders, use_container_width=True, hide_index=True)

# # PIPELINE + RISK
# left, right = st.columns(2)
# pipeline = pd.DataFrame({
#     "Stage": ["Identified", "Drafting", "Review", "Submitted"],
#     "Count": [42, 18, 11, 7]
# })
# risk = pd.DataFrame({
#     "Type": ["Missing Docs", "Legal", "Format"],
#     "Count": [6, 3, 2]
# })

# with left:
#     st.markdown("### Tender Pipeline")
#     fig1 = px.bar(pipeline, x="Stage", y="Count", template="plotly_dark", height=220)
#     fig1.update_layout(margin=dict(l=10, r=10, t=30, b=10))
#     st.plotly_chart(fig1, use_container_width=True)

# with right:
#     st.markdown("### Risk Snapshot")
#     fig2 = px.bar(risk, x="Type", y="Count", template="plotly_dark", height=220)
#     fig2.update_layout(margin=dict(l=10, r=10, t=30, b=10))
#     st.plotly_chart(fig2, use_container_width=True)

# # ALERTS + AI TRUST
# a1, a2 = st.columns([1.2, 1])
# with a1:
#     st.markdown("### Alerts")
#     st.error("Mumbai Metro — Financial annexure missing")
#     st.warning("NH Infra — Clause mismatch detected")

# with a2:
#     st.markdown("### AI Trust Status")
#     st.success("✔ RAG Verification Active")
#     st.success("✔ Local Embeddings Enabled")
#     st.info("1 tender pending manual review")

# # FOOTER
# st.caption("TenderFlow AI • Secure • Compliant • Hallucination-Proof")



import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from pathlib import Path
import os
from supabase import create_client
#from components.navbar import render_navbar
import base64

#UTILS
def get_base64_of_bin_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

if not st.session_state.get("authenticated"):
    st.switch_page("pages/loginPage.py")
    st.stop()

if not st.session_state.get("onboarding_complete"):
    step = st.session_state.get("onboarding_step", 1)
    st.switch_page(f"pages/informationCollection_{step}.py")

user = st.session_state["user"]

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase environment variables not loaded")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

#auth_and_onboarding_guard(supabase)

# Page config
st.set_page_config(page_title="Dashboard", layout="wide", initial_sidebar_state="collapsed")

logo_path = Path(__file__).resolve().parents[1]/"assets"/"logo.png"
logo_base64 = get_base64_of_bin_file(logo_path)

#render_navbar()

# Custom CSS
st.markdown("""
<style>
    /* Main theme */
    .stApp {
        background: #0f111a;
    }
    
    /* Hide default sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }
            
    /* Hide Streamlit top bar (Deploy, menu, etc.) */
        header[data-testid="stHeader"] {
            display: none;
        }

/* Remove extra top padding Streamlit adds */
.stApp {
    margin-top: -80px;
}
    
    /* Left Navigation Bar */
    .left-nav {
        position: fixed;
        left: 0;
        top: 0;
        width: 70px;
        height: 100vh;
        background: #0f111a;
        border-right: 1px solid #252a4a;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding-top: 1rem;
        z-index: 1000;
        box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
    }
    
    .nav-icon {
        width: 45px;
        height: 45px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0.5rem 0;
        border-radius: 8px;
        cursor: pointer;
        transition: background-color 0.2s;
        color: #9ca3af;
        font-size: 1.5rem;
    }
    
    .nav-icon:hover {
        background-color: #1b1f3b;
        color: e5e7eb;
    }
    
    .nav-icon.active {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white;
    }
    
    /* Main content area with left margin */
    .main-content {
        margin-left: 70px;
        padding: 0 2rem;
    }
    
    /* Header styling */
    .top-header {
        background-color: #0f111a;
        padding: 1rem 2rem;
        border-top: 1px solid #252a4a;
        border-bottom: 1px solid #252a4a;
        margin: -2rem -3rem 2rem -2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .logo-section {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1.5rem;
        font-weight: 700;
        color: #e5e7eb;
    }
    
    .dashboard-title {
        font-size: 1.75rem;
        font-weight: 600;
        color: #e5e7eb;
        margin-bottom: 0.25rem;
    }
    
    .dashboard-date {
        font-size: 0.875rem;
        color: #9ca3af;
    }
    
    /* KPI Card styling */
    .kpi-card {
        background: linear-gradient(135deg, #1b1f3b 0%, #14172a 100%);
        border: 1px solid #252a4a;
        border-radius: 12px;
        padding: 1.5rem;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        height: 100%;
        position: relative;
    }
    
    .kpi-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
        font-size: 0.875rem;
        opacity: 0.9;
        color: #9ca3af;
    }
    
    .kpi-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #e5e7eb;
    }
    
    .kpi-footer {
        font-size: 0.75rem;
        opacity: 0.7;
        color: #6b7280;
    }
    
    /* Chart card styling */
    .chart-card {
        background: #14172a;
        border: 1px solid #252a4a;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
        height: 100%;
        margin-top: -35px;
        margin-bottom: 25px;
    }
    
    .chart-title {
        font-size: 1rem;
        font-weight: 600;
        color: #e5e7eb;
        margin-bottom: 0.5rem;
    }
    
    .chart-subtitle {
        font-size: 0.75rem;
        color: #9ca3af;
        margin-bottom: 1rem;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# Left Navigation Bar (Fixed)
st.markdown("""
<div class="left-nav">
    <div class="nav-icon active" title="Dashboard">📊</div>
    <div class="nav-icon" title="List">☰</div>
    <div class="nav-icon" title="Bookmark">🔖</div>
    <div class="nav-icon" title="Calendar">📅</div>
    <div class="nav-icon" title="Users">👤</div>
    <div style="flex: 1;"></div>
    <div class="nav-icon" title="Settings">✏️</div>
    <div class="nav-icon" title="Profile">
        <div style="width: 35px; height: 35px; border-radius: 50%; background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);"></div>
    </div>
    <div style="font-size: 0.65rem; color: #64748b; margin-top: 0.5rem;">v2.8.6</div>
</div>
""", unsafe_allow_html=True)

# Main content wrapper
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Top Header
st.markdown(f"""
<div class="top-header">
    <div class="logo-section">
        {"<img src= 'data: image/png;base64," + logo_base64 + "' style= 'height: 60px; width: auto;' />" if logo_base64 else ""}
    </div>
    <div style="display: flex; gap: 1rem; align-items: center;">
        <span style="color: #64748b; cursor: pointer;">What's New</span>
        <span style="font-size: 1.5rem; cursor: pointer;">🔔</span>
    </div>
</div>
""", unsafe_allow_html=True) 

# Dashboard header
st.markdown('<div class="dashboard-title">Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-date">Friday, 26 March 2021</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Filters
filter_col1, filter_col2, filter_col3, filter_col4, filter_col5, filter_col6 = st.columns(6)
with filter_col1:
    date_range = st.selectbox("Date Range", ["All Time", "Last Week", "Last Month", "Last Quarter"])
with filter_col2:
    type_filter = st.selectbox("Type", ["All", "Federal", "State", "Commercial"])
with filter_col3:
    status_filter = st.selectbox("Status", ["All", "Active", "Won", "Lost"])
with filter_col4:
    customer_filter = st.selectbox("Customer", ["All", "Customer A", "Customer B"])
with filter_col5:
    priority_filter = st.selectbox("Priority", ["All", "High", "Medium", "Low"])
with filter_col6:
    business_line = st.selectbox("Business Line", ["All", "IT", "Consulting", "Engineering"])

st.markdown("<br>", unsafe_allow_html=True)

# KPI Cards Row
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-header">💰 Project Value Won</div>
        <div class="kpi-value">$802.21M</div>
        <div class="kpi-footer">All Time</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-header">📈 Win / Loss Ratio</div>
        <div class="kpi-value">23:6</div>
        <div class="kpi-footer">All Time</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-header">✓ Capture Ratio</div>
        <div class="kpi-value">$802.21M : $1.6B</div>
        <div style="background-color: rgba(255,255,255,0.2); height: 8px; border-radius: 4px; margin-top: 1rem;">
            <div style="background-color: #60a5fa; height: 100%; width: 50%; border-radius: 4px;"></div>
        </div>
        <div class="kpi-footer">All Time</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-header">⬇ Registered Opportunities</div>
        <div class="kpi-value">101</div>
        <div class="kpi-footer">All Time</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# Charts Row
chart_col1, chart_col2, chart_col3 = st.columns([1, 1, 1])

with chart_col1:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">Bid Activity</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-subtitle">STATUS (ALL TIME)</div>', unsafe_allow_html=True)
    
    # Donut chart data
    labels = ['Registered', 'In Progress', 'Submitted', 'Won', 'Lost', 'Withdrawn', 'Other']
    values = [28, 7, 15, 25, 12, 8, 6]
    colors = ["#6366f1",
    "#38bdf8",
    "#22c55e",
    "#4f46e5",
    "#ef4444",
    "#f59e0b",
    "#6b7280"]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker=dict(colors=colors),
        textinfo='none',
        hovertemplate='<b>%{label}</b><br>%{value} opportunities<extra></extra>'
    )])
    
    fig.update_layout(
        showlegend=False,
        height=300,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('<div style="text-align: center; font-size: 0.875rem; color: #64748b; margin-top: 1rem;">Total Opportunities: 101</div>', unsafe_allow_html=True)
    
    # Status breakdown
    st.markdown('<div style="margin-top: 1rem;">', unsafe_allow_html=True)
    for label, value in [('Registered', 28), ('In Progress', 7), ('Submitted', 15)]:
        st.markdown(f'<div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-top: 1px solid #f1f5f9;"><span>{'▶' if label == 'In Progress' else '▼'} {label}</span><span>{value}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with chart_col2:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">Bid / No Bid</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-subtitle">DECISION (ALL TIME)</div>', unsafe_allow_html=True)
    
    # Horizontal bar chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=['Bid', 'No Bid'],
        x=[66, 33],
        orientation='h',
        marker=dict(color=['#6366f1', '#94a3b8']),
        text=['66%', '33%'],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>%{x}%<extra></extra>'
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(t=20, b=20, l=0, r=0),
        xaxis=dict(showgrid=False, showticklabels=False, range=[0, 100]),
        yaxis=dict(showgrid=False),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('<div style="text-align: center; font-size: 0.875rem; color: #64748b; margin-top: 1rem;">Average bid score: 62.22</div>', unsafe_allow_html=True)
    
    # # Bid Activity over time
    # st.markdown('<div class="chart-title" style="margin-top: 2rem;">Bid Activity</div>', unsafe_allow_html=True)
    # st.markdown('<div class="chart-subtitle">OPPORTUNITIES REGISTERED (ALL TIME)</div>', unsafe_allow_html=True)
    
    # # Time series data
    # dates = pd.date_range(start='2018-07-01', end='2021-03-01', freq='MS')
    # values = np.random.poisson(3, len(dates))
    # values[-3:] = [7, 8, 6]  # Peak at the end
    
    # fig = go.Figure()
    # fig.add_trace(go.Bar(
    #     x=dates,
    #     y=values,
    #     marker=dict(color='#3b82f6'),
    #     hovertemplate='<b>%{x|%b %Y}</b><br>%{y} opportunities<extra></extra>'
    # ))
    
    # fig.update_layout(
    #     height=250,
    #     margin=dict(t=0, b=0, l=0, r=0),
    #     xaxis=dict(showgrid=False),
    #     yaxis=dict(showgrid=True, gridcolor='#252a4a', range=[0, 10]),
    #     paper_bgcolor='rgba(0,0,0,0)',
    #     plot_bgcolor='rgba(0,0,0,0)',
    #     showlegend=False
    # )
    
    # st.plotly_chart(fig, use_container_width=True)
    
    #st.markdown('<div style="text-align: center; font-size: 0.875rem; color: #64748b; margin-top: 0.5rem;">Total Opportunities: 101</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with chart_col3:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">Resource Allocation</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-subtitle">TASKS (ALL TIME)</div>', unsafe_allow_html=True)
    
    # Resource allocation data
    resources = [
        ("Aaron Godde", 30, 36, "#3b82f6"),
        ("Aleck Bassingthwaite", 26, 31, "#3b82f6"),
        ("Nyree McKenzie", 23, 28, "#3b82f6"),
        ("Carol Wilson", 15, 18, "#3b82f6"),
        ("Aaron Godde (2)", 2, 3, "#e2e8f0"),
        ("Tyson Young", 1, 2, "#e2e8f0"),
        ("Adrian Liu", 0, 0, "#e2e8f0")
    ]
    
    for i, (name, percent, tasks, color) in enumerate(resources):
        col_a, col_b, col_c, col_d = st.columns([0.15, 0.4, 0.3, 0.15])
        
        with col_a:
            st.markdown(f'<div style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #3b82f6 0%, #38bdf8 100%); display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 0.875rem;">{name[0]}</div>', unsafe_allow_html=True)
        
        with col_b:
            st.markdown(f'<div style="padding-top: 0.5rem; font-size: 0.875rem; color: white;">{name.split("(")[0].strip()}</div>', unsafe_allow_html=True)
        
        with col_c:
            st.markdown(f'<div style="padding-top: 0.5rem;"><div style="display: flex; align-items: center; gap: 0.5rem;"><span style="font-size: 0.75rem; color: white; min-width: 35px;">{percent}%</span><div style="flex: 1; height: 8px; background-color: #252a4a; border-radius: 4px; overflow: hidden;"><div style="height: 100%; background: {color}; width: {percent}%; border-radius: 4px;"></div></div></div></div>', unsafe_allow_html=True)
        
        with col_d:
            st.markdown(f'<div style="padding-top: 0.5rem; text-align: right; font-size: 0.875rem; color: white;">{tasks}</div>', unsafe_allow_html=True)
        
        if i < len(resources) - 1:
            st.markdown('<div style="border-bottom: 1px solid #64748b; margin: 0.5rem 0;"></div>', unsafe_allow_html=True)
    
    st.markdown('<div style="text-align: center; font-size: 0.875rem; color: #64748b; margin-top: 1.5rem; padding-top: 1rem; border-top: 2px solid #f1f5f9;">Total tasks: 119</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Bottom section
st.markdown("<br>", unsafe_allow_html=True)

#bottom_col1, bottom_col2 = st.columns(2)

#with bottom_col1:
#    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
#    st.markdown('<div class="chart-title">Top 10 Customers</div>', unsafe_allow_html=True)
#   st.markdown('<div class="chart-subtitle">OPPORTUNITIES (ALL TIME)</div>', unsafe_allow_html=True)
#   st.markdown('</div>', unsafe_allow_html=True)

# Close main content wrapper
#st.markdown('</div>', unsafe_allow_html=True)