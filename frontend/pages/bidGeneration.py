import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import base64
from pathlib import Path
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="TenderFlow | AI Bid Suite", layout="wide", initial_sidebar_state="collapsed")

def get_base64_of_bin_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
logo_base64 = get_base64_of_bin_file(logo_path)

# --- UTILS (Shared styling for all pages) ---
def local_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        .stApp { background-color: #0f111a; color: #e5e7eb; font-family: 'Inter', sans-serif; }
        
        /* Glassmorphism Cards */
        .card {
            background: #14172a;
            border: 1px solid #252a4a;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }

        /* Top Header Navigation Box Styling */
        .nav-right-container { display: flex; align-items: center; gap: 10px; margin-left: auto; }
        .nav-right-container .stButton button {
            background: transparent !important; border: 1px solid #252a4a !important;
            color: #9ca3af !important; width: 40px !important; height: 40px !important;
            border-radius: 8px !important; display: flex !important; align-items: center !important;
            justify-content: center !important; padding: 0 !important;
        }
        .nav-right-container .stButton button:hover { border-color: #6366f1 !important; color: white !important; }

        /* KPI & Bid Price Styling */
        .bid-highlight {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-left: 4px solid #6366f1;
            padding: 25px;
            border-radius: 12px;
            text-align: center;
        }
        .price-text { font-size: 2.8rem; font-weight: 800; color: #60a5fa; font-family: monospace; }
        
        /* Custom Labels */
        .section-label { color: #9ca3af; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)



# --- LOGIC FUNCTIONS ---
def calculate_ai_confidence(final_bid, prime_cost, overhead, profit):
    market_benchmark = 78000 
    price_score = np.exp(-2.8 * (final_bid / market_benchmark - 0.75)**2)
    efficiency_score = 1.0 - (overhead / 40) 
    margin_score = np.clip(1 - abs(profit - 15)/30, 0, 1)
    weighted_score = (price_score * 0.6) + (efficiency_score * 0.2) + (margin_score * 0.2)
    return np.clip(weighted_score, 0.05, 0.98)

def render_header():
    # Placeholder for logo and horizontal nav

    logo_html = f"<img src='data:image/png;base64,{logo_base64}' style='height:70px; width:auto;' />" if logo_base64 else ""
    h_col1, h_col2 = st.columns([1, 4])
    with h_col1:
        st.markdown(f'''<div>{logo_html}</div ''', unsafe_allow_html=True)
        #st.markdown("<h2 style='color:white; margin:0;'>TenderFlow</h2>", unsafe_allow_html=True)
    with h_col2:
        # Integrated Horizontal Nav Icons
        nav_cols = st.columns([5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
        with nav_cols[1]: st.button("⊞", key="nav_d")
        with nav_cols[2]: st.button("✦", key="nav_b")
        with nav_cols[3]: st.button("◈", key="nav_a")
        with nav_cols[4]: st.button("⎘", key="nav_g")
        with nav_cols[5]: st.button("⬈", key="nav_r")
        with nav_cols[6]: st.button("⚙", key="nav_s")
        with nav_cols[7]: st.button("👤", key="nav_p")

def bid_generation_page():
    local_css()
    render_header()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- PHASE 1: INITIALIZATION ---
    if 'extraction_done' not in st.session_state:
        st.markdown("<div style='text-align:center; padding: 50px 0;'>", unsafe_allow_html=True)
        #st.title("✦ Smart Bid Extraction")
        st.markdown(
            "<h1 style='text-align:left;'>✦ Smart Bid <span style='color:#a855f7;'>Extraction</span></h1>",
            unsafe_allow_html=True
        )
        st.write("Upload your technical specification to auto-calculate labor and material costs.")
        
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            uploaded_file = st.file_uploader("Upload Tender PDF", type="pdf", label_visibility="collapsed")
            if uploaded_file:
                with st.status("Analyzing document structure...", expanded=True):
                    time.sleep(1.5)
                    st.session_state.extraction_done = True
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # --- PHASE 2: ACTIVE DASHBOARD ---
    st.markdown("### ✍️ Bid Configuration")
    
    col_main, col_side = st.columns([2, 1], gap="medium")

    with col_main:
        # Task Ledger
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-label">1. Resource & Task Ledger</p>', unsafe_allow_html=True)
        
        if 'cost_df' not in st.session_state:
            st.session_state.cost_df = pd.DataFrame([
                {"Task": "Core Backend Architecture", "Qty": 180, "Rate": 95},
                {"Task": "Frontend UI/UX Implementation", "Qty": 320, "Rate": 75},
                {"Task": "API Integration & Testing", "Qty": 140, "Rate": 85},
            ])

        edited_df = st.data_editor(st.session_state.cost_df, use_container_width=True, num_rows="dynamic")
        total_prime = (edited_df['Qty'] * edited_df['Rate']).sum()
        
        st.markdown(f"<div style='text-align:right; font-weight:bold; color:#60a5fa;'>Subtotal Prime Cost: ${total_prime:,.2f}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Strategy
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-label">2. Pricing Strategy</p>', unsafe_allow_html=True)
        s_c1, s_c2 = st.columns(2)
        overhead_pct = s_c1.number_input("Overhead (%)", 0, 100, 12)
        profit_pct = s_c2.slider("Profit Margin (%)", 5, 50, 15)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_side:
        # Final Result Box
        base_total = total_prime * (1 + (overhead_pct / 100))
        final_bid = base_total * (1 + (profit_pct / 100))
        
        st.markdown(f"""
            <div class="bid-highlight">
                <p class="section-label" style="color:#a5b4fc">Optimized Bid Value</p>
                <div class="price-text">${final_bid:,.0f}</div>
                <p style="color:#94a3b8; font-size:0.9rem;">Total Margin: ${(final_bid - total_prime):,.0f}</p>
            </div>
        """, unsafe_allow_html=True)

        # AI Confidence Gauge
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-label">AI Win Probability</p>', unsafe_allow_html=True)
        
        win_prob = calculate_ai_confidence(final_bid, total_prime, overhead_pct, profit_pct)
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = win_prob * 100,
            number = {'suffix': "%", 'font': {'color': 'white'}},
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#6366f1"}, 'bgcolor': "#1e293b"}
        ))
        fig.update_layout(height=180, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        
        if win_prob > 0.7:
            st.success("High win probability based on market trends.")
        else:
            st.warning("Price may be too high for this sector.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Footer Actions
    st.divider()
    f1, f2, f3 = st.columns([4, 1, 1])
    with f2: st.button("💾 Save Progress", use_container_width=True)
    with f3: st.button("🚀 Export Proposal", type="primary", use_container_width=True)

if __name__ == "__main__":
    bid_generation_page()