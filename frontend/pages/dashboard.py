import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from pathlib import Path
import os
from supabase import create_client
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

# ---------------- HANDLE SIDEBAR NAV ----------------
nav_page = st.query_params.get("nav")
if nav_page:
    st.switch_page(nav_page)


logo_path = Path(__file__).resolve().parents[1]/"assets"/"logo.png"
logo_base64 = get_base64_of_bin_file(logo_path)

#render_navbar()

# Custom CSS
st.markdown("""
<style>
    .stApp { background: #0f111a; margin-top: -80px;}
    
    [data-testid="stSidebar"] {display: none;}
    header[data-testid="stHeader"] {display: none;}
    
    /* Main content area with left margin */
    .main-content {
        margin-left: 70px;
        padding: 0 2rem;
    }
    
    /* Header styling */
    .top-header {
        background-color: #0f111a;
        padding: 10px 20px;
        border-top: 1px solid #252a4a;
        border-bottom: 1px solid #252a4a;
        margin: 2rem;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
    }
            
    .nav-btn button{
        background: transparent !important;
        border: none !important;
        font-size: 1.4rem !important;
        color: #9ca3af !important;        
    }
            
    .nav-btn button:hover {
        color: #e5e7eb !important;
    }
    
    .nav-horizontal {
    display: flex;
    gap: 10px;
    align-items: center;
}

.nav-right-container {
    display: flex;
    align-items: center;
    gap: 12px;           /* Icons ke beech ki barabar doori */
    margin-left: auto;   /* Ye icons ko right side push kar dega */
    padding-right: 20px;
}

.nav-right-container .stButton button {
    background: transparent !important;
    border: 1px solid #252a4a !important;
    color: #9ca3af !important;
    font-size: 1.1rem !important;
    width: 38px !important;
    height: 38px !important;
    border-radius: 6px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 !important;
}

.nav-right-container .stButton button:hover {
    border-color: #6366f1 !important;
    background: #1b1f3b !important;
    color: white !important;
}        
    
    .logo-section {
        display: flex;
        align-items: center;
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

# Logo base64 check
logo_html = f"<img src='data:image/png;base64,{logo_base64}' style='height:70px; width:auto;' />" if logo_base64 else ""

# Header HTML Start
st.markdown(f'''
    <div class="top-header">
        <div class="logo-section">
            {logo_html}
        </div>
        <div class="nav-right-container" id="nav-root">
''', unsafe_allow_html=True)

header_cols = st.columns([6, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4])

with header_cols[1]:
    if st.button("⊞", key="h_dash", help="Dashboard"): st.switch_page("app.py")
with header_cols[2]:
    if st.button("✦", key="h_bid", help="Bid Generation"): st.switch_page("pages/bidGeneration.py")
with header_cols[3]:
    if st.button("◈", key="h_anl", help="Tender Analysis "): st.switch_page("pages/tenderAnalyser.py")
with header_cols[4]:
    if st.button("⎘", key="h_gen", help="Tender Generation"): st.switch_page("pages/tenderGeneration.py")
with header_cols[5]:
    if st.button("⬈", key="h_risk", help="Risk Analysis"): st.switch_page("pages/riskAnalysis.py")
with header_cols[6]:
    if st.button("⚙", key="h_set", help="Settings"): st.switch_page("pages/settings.py")
with header_cols[7]:
    if st.button("👤", key="h_prof", help="Profile"): st.switch_page("pages/profile.py")

st.markdown('</div></div>', unsafe_allow_html=True)
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
        <div class="kpi-value">₹802.21M</div>
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
        <div class="kpi-value">₹802.21M : ₹1.6B</div>
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
    st.markdown('<div class="chart-title">Tenders by Category</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-subtitle">BUMBER OF TENDERS(ALL TIME)</div>', unsafe_allow_html=True)

    #Tenders per ccategory
    categories = ['Federal', 'State', 'Commercial', 'Other']
    tender_counts = [45, 30, 20, 6] #Replacement of real data for NOW
    colors =['#6366f1','#38bdf8','#22c55e','#f59e0b']
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=categories,y=tender_counts,marker_color=colors,text=tender_counts,textposition='auto',hovertemplate='<b>%{x}</b><b>%{y} tenders<extra></extra>'))
    fig.update_layout(height=250, margin=dict(t=20, b=20, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',xaxis=dict(showgrid=False),yaxis=dict(showgrid=True, gridcolor='#252a4a'),showlegend=False)

    st.plotly_chart(fig, use_container_width=True)
    st.markdown('<div style="text=align: center; font-size: 0.875rem; color: #64748b; margin-top: 1rem;">Total Tenders: {}</div>'.format(sum(tender_counts)), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

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
    st.markdown('<div class="chart-title">Top Higehest Bids</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-subtitle">BY VALUE(ALL TIME)</div>', unsafe_allow_html=True)
    
    highest_bids = [("P ALpha", 15_200_000),("P Beta", 12_500_000),("P Gamma", 9_800_000), ("P Delta", 7_600_000),("P Epsilsom", 5_00_000)]

    for i, (project, value) in enumerate(highest_bids):
        st.markdown(f'''
        <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #64748b;">
            <span style="font-weight: 600; color: white;">{i+1}.{project}</span>
            <span style="color: #60a5fa; font-weight: 600;">₹{value/1_000_000:.1f}M</span>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown(f'<div style="text-align: center; font-size: 0.875rem; color: #64748b; margin-top: 1rem;">Total Bids Listed: {len(highest_bids)}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    # # Resource allocation data
    # resources = [
    #     ("Aaron Godde", 30, 36, "#3b82f6"),
    #     ("Aleck Bassingthwaite", 26, 31, "#3b82f6"),
    #     ("Nyree McKenzie", 23, 28, "#3b82f6"),
    #     ("Carol Wilson", 15, 18, "#3b82f6"),
    #     ("Aaron Godde (2)", 2, 3, "#e2e8f0"),
    #     ("Tyson Young", 1, 2, "#e2e8f0"),
    #     ("Adrian Liu", 0, 0, "#e2e8f0")
    # ]
    
    # for i, (name, percent, tasks, color) in enumerate(resources):
    #     col_a, col_b, col_c, col_d = st.columns([0.15, 0.4, 0.3, 0.15])
        
    #     with col_a:
    #         st.markdown(f'<div style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #3b82f6 0%, #38bdf8 100%); display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 0.875rem;">{name[0]}</div>', unsafe_allow_html=True)
        
    #     with col_b:
    #         st.markdown(f'<div style="padding-top: 0.5rem; font-size: 0.875rem; color: white;">{name.split("(")[0].strip()}</div>', unsafe_allow_html=True)
        
    #     with col_c:
    #         st.markdown(f'<div style="padding-top: 0.5rem;"><div style="display: flex; align-items: center; gap: 0.5rem;"><span style="font-size: 0.75rem; color: white; min-width: 35px;">{percent}%</span><div style="flex: 1; height: 8px; background-color: #252a4a; border-radius: 4px; overflow: hidden;"><div style="height: 100%; background: {color}; width: {percent}%; border-radius: 4px;"></div></div></div></div>', unsafe_allow_html=True)
        
    #     with col_d:
    #         st.markdown(f'<div style="padding-top: 0.5rem; text-align: right; font-size: 0.875rem; color: white;">{tasks}</div>', unsafe_allow_html=True)
        
    #     if i < len(resources) - 1:
    #         st.markdown('<div style="border-bottom: 1px solid #64748b; margin: 0.5rem 0;"></div>', unsafe_allow_html=True)
    
    # st.markdown('<div style="text-align: center; font-size: 0.875rem; color: #64748b; margin-top: 1.5rem; padding-top: 1rem; border-top: 2px solid #f1f5f9;">Total tasks: 119</div>', unsafe_allow_html=True)
    # st.markdown('</div>', unsafe_allow_html=True)

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