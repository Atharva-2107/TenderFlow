import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Page Setup
st.set_page_config(page_title="TenderFlow AI", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS FOR COLORFUL & VIBRANT UI ---
st.markdown("""
    <style>
    /* Main Background Gradient */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
    }
    
    /* Top Navbar with Glow */
    header[data-testid="stHeader"] {
        background-color: #1e293b;
        border-bottom: 2px solid #3b82f6;
    }

    /* Sidebar - Glassmorphism style */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.8);
        border-right: 1px solid #3b82f6;
    }

    /* Card Design: Colorful Borders & Backgrounds */
    .dashboard-card {
        background: rgba(30, 41, 59, 0.7);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid #3b82f6;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2);
        margin-bottom: 20px;
    }

    /* Vibrant Buttons */
    .stButton>button {
        background: linear-gradient(45deg, #3b82f6, #8b5cf6);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 15px #3b82f6;
    }

    /* Text Colors */
    h1, h2, h3 { color: #60a5fa !important; }
    p, span, label { color: #e2e8f0 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- TOP NAVBAR ---
nav_col1, nav_col2, nav_col3 = st.columns([0.2, 0.6, 0.2])
with nav_col1:
    st.markdown("<h2 style='margin-top:-40px;'>TenderFlow</h2>", unsafe_allow_html=True)
with nav_col2:
    st.markdown("<p style='text-align:center; margin-top:-20px; color:#94a3b8;'>Automated Tender Engineering Pipeline</p>", unsafe_allow_html=True)
with nav_col3:
    # Profile Section matching wireframe
    with st.popover("👤 Profil"):
        st.markdown("### User Profile")
        st.write("**Name:** Atharva Chavan [cite: 9, 126]")
        st.write("**Institution:** K.J Somaiya [cite: 8]")
        st.write("**Team:** Astra [cite: 7]")
        st.button("Logout")

# --- SIDEBAR (Persistent Navigation) ---
with st.sidebar:
    st.markdown("<h3 style='color:#8b5cf6;'>Menu</h3>", unsafe_allow_html=True)
    selection = st.radio(
        "Navigation",
        ["Dashboard", "Tender Generations", "Bid Generation", "Risk Analytics", "Prompt Bot", "Settings"],
        label_visibility="collapsed"
    )
    st.divider()
    st.markdown("🔥 **Live Status: Groq GenAI Active** [cite: 31]")

# --- MAIN DASHBOARD AREA ---
if selection == "Dashboard":
    # Grid Layout per Wireframe
    main_col, side_col = st.columns([0.7, 0.3])

    with main_col:
        # 1. Recents Bids
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.subheader("📋 Recent Bids")
        bid_data = pd.DataFrame({
            "ID": ["TR-2026", "MH-4091", "IN-882"],
            "Task": ["Methodology Draft", "Cost Optimization", "Compliance Check"],
            "Speed": ["97% Faster [cite: 31]", "Active", "Verified [cite: 79]"]
        })
        st.dataframe(bid_data, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 2. Recent Activity Graphs (Colorful Plotly Chart)
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.subheader("📈 Activity Trends")
        chart_data = pd.DataFrame({
            'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
            'Bids Generated': [5, 12, 8, 15, 10]
        })
        fig = px.line(chart_data, x='Day', y='Bids Generated', markers=True)
        fig.update_traces(line_color='#8b5cf6', line_width=4)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#e2e8f0")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with side_col:
        # 3. Market Trends
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.subheader("📊 Market Trends")
        st.metric("Efficiency Gain", "97% [cite: 31]", delta="FastTrack")
        st.metric("Success Rate", "89%", delta="High")
        st.write("**AI Note:** Dynamic Cost Intelligence suggests the 'Sweet Spot' bid based on historical data[cite: 82, 83].")
        st.markdown('</div>', unsafe_allow_html=True)

    # 4. Action Buttons (Bottom Right)
    btn_col1, btn_col2, btn_col3 = st.columns([0.6, 0.2, 0.2])
    with btn_col2:
        if st.button("Generate Bid"):
            st.toast("Using Llama-3.3-70b to draft technical methodology... [cite: 55]")
    with btn_col3:
        st.button("View All Data")

elif selection == "Risk Analytics":
    st.title("🛡️ Risk & Compliance Engine")
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.write("### Hallucination-Proof RAG [cite: 78]")
    st.write("2-stage verification system using **FlashRank** to double-check AI answers against original PDF evidence[cite: 79].")
    st.progress(0.99, text="Compliance Accuracy: 99%")
    st.markdown('</div>', unsafe_allow_html=True)