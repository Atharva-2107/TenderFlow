import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="TenderFlow | AI Bid Suite",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 0. HELPER: INDIAN CURRENCY FORMATTER (THE FEATURE) ---
def format_inr(number):
    """
    Formats a number into Indian System (Lakhs/Crores)
    Example: 1234567 -> 12,34,567.00
    """
    s, *d = str(f"{number:.2f}").partition(".")
    r = ",".join([s[x-2:x] for x in range(-3, -len(s), -2)][::-1] + [s[-3:]])
    return "₹" + "".join([r] + d)

def calculate_ai_confidence(final_bid, prime_cost, overhead, profit):
    """
    Simulates a multi-factor AI scoring engine.
    In production, this would be a call to your FastAPI /predict-win endpoint.
    """
    # Factor 1: Market Benchmark (Updated for Civil Scale ~ 15 Lakhs)
    market_benchmark = 1500000 
    price_score = np.exp(-5.5 * (final_bid / market_benchmark - 0.85)**2)
    
    # Factor 2: Efficiency Score (Ratio of Overhead vs Prime)
    efficiency_score = 1.0 - (overhead / 50) 
    
    # Factor 3: Margin Health
    margin_score = np.clip(1 - abs(profit - 12)/25, 0, 1)
    
    # Weighted Average
    weighted_score = (price_score * 0.6) + (efficiency_score * 0.2) + (margin_score * 0.2)
    return np.clip(weighted_score, 0.05, 0.98)

def bid_generation_page():
    # --- 1. MODERN DARK & PURPLE STYLING ---
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
        
        .stApp { background-color: #09090B; color: #FAFAFA; font-family: 'Inter', sans-serif; }
        .glass-card {
            background: rgba(24, 24, 27, 0.8);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(63, 63, 70, 0.5);
            margin-bottom: 20px;
        }
        .bid-box {
            background: linear-gradient(135deg, #6D28D9 0%, #4C1D95 100%);
            border-radius: 16px;
            padding: 32px;
            text-align: center;
            box-shadow: 0 0 30px rgba(139, 92, 246, 0.2);
            border: 1px solid rgba(167, 139, 250, 0.3);
        }
        .bid-price {
            font-family: 'JetBrains Mono', monospace;
            font-size: 3.2rem;
            font-weight: 700;
            color: #FFFFFF;
            letter-spacing: -2px;
        }
        .label-text { color: #A1A1AA; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; }
        .stButton>button { border-radius: 10px; background-color: #7C3AED; color: white; border: none; font-weight: 600; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

    # --- 2. HEADER AREA ---
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown("<h1 style='margin-bottom: 0;'>TenderFlow <span style='color: #A855F7;'>AI</span></h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #71717A;'>Smart Bid Generation & Optimization Engine</p>", unsafe_allow_html=True)
    
    # --- 3. INITIALIZATION LOGIC ---
    if 'extraction_done' not in st.session_state:
        st.markdown("<br><br>", unsafe_allow_html=True)
        _, col_mid, _ = st.columns([1, 2, 1]) 
        
        with col_mid:
            # st.markdown('<div class="glass-card" style="text-align: center;">', unsafe_allow_html=True)
            st.markdown("### 📂 Initialize New Bid")
            st.write("Upload your technical proposal to begin AI cost extraction.")
            
            uploaded_tender = st.file_uploader("Drop PDF here", type=['pdf'], label_visibility="collapsed")
            
            if uploaded_tender:
                with st.status("🔮 Analyzing with Llama-3.3...", expanded=True):
                    time.sleep(1.5) 
                    st.session_state.extraction_done = True
                    st.rerun() 
            st.markdown('</div>', unsafe_allow_html=True)
        return 

    # --- 4. DASHBOARD VIEW ---
    st.divider()
    left_col, right_col = st.columns([1.8, 1.2], gap="large")

    with left_col:
        # st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="label-text">Resource Ledger</p>', unsafe_allow_html=True)
        
        # --- DATA UPDATED FOR CIVIL ENGINEERING ---
        if 'cost_df' not in st.session_state:
            st.session_state.cost_df = pd.DataFrame([
                {"Task": "Excavation (Machine)", "Qty": 1500, "Rate": 300},
                {"Task": "PCC M15 (Foundation)", "Qty": 200, "Rate": 4500},
                {"Task": "RCC M25 (Columns)", "Qty": 150, "Rate": 5200},
                {"Task": "Steel Reinforcement (Kg)", "Qty": 2500, "Rate": 72},
            ])

        edited_df = st.data_editor(
            st.session_state.cost_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Rate": st.column_config.NumberColumn(format="₹%d"), 
                "Qty": st.column_config.NumberColumn(step=1),
            }
        )
        total_prime = (edited_df['Qty'] * edited_df['Rate']).sum()
        
        # --- FEATURE: Apply Indian Formatting to Prime Cost ---
        prime_display = format_inr(total_prime)
        
        st.markdown(f"<div style='text-align: right; color: #A855F7; font-family: JetBrains Mono; font-size: 1.2rem;'>Prime Cost: {prime_display}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="label-text">Pricing Strategy</p>', unsafe_allow_html=True)
        c_s1, c_s2 = st.columns(2)
        overhead_pct = c_s1.slider("Overhead Recovery (%)", 0, 30, 12)
        profit_pct = c_s2.select_slider("Target Profit (%)", options=[5, 10, 15, 20, 25, 30], value=15)
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        # FINAL PROPOSAL CALCULATION
        base_total = total_prime * (1 + (overhead_pct / 100))
        final_bid = base_total * (1 + (profit_pct / 100))
        gross_profit = final_bid - total_prime

        # --- FEATURE: Apply Indian Formatting to Bid & Profit ---
        final_bid_display = format_inr(final_bid)
        gross_profit_display = format_inr(gross_profit)
        
        st.markdown(f"""
            <div class="bid-box">
                <div class="label-text" style="color: #DDD6FE;">Final Optimized Bid</div>
                <div class="bid-price">{final_bid_display}</div>
                <div style="font-size: 0.85rem; color: #C4B5FD; opacity: 0.9;">
                    Gross Profit: {gross_profit_display}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        # AI WIN CONFIDENCE LOGIC
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="label-text">AI Win Confidence</p>', unsafe_allow_html=True)
        
        win_prob = calculate_ai_confidence(final_bid, total_prime, overhead_pct, profit_pct)

        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = win_prob * 100,
            number = {'suffix': "%", 'font': {'color': '#FAFAFA', 'family': "JetBrains Mono"}},
            gauge = {
                'axis': {'range': [0, 100], 'visible': False},
                'bar': {'color': "#A855F7"},
                'bgcolor': "#27272A",
                'borderwidth': 0,
            }
        ))
        fig.update_layout(height=160, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        
        # Dynamic Feedback
        if win_prob > 0.8:
            st.success("✅ **Strong Positioning:** Your pricing is optimized for current market saturation.")
        elif win_prob > 0.5:
            st.warning("⚖️ **Competitive Baseline:** Standard bidding range detected.")
        else:
            st.error("🚨 **Low Probability:** Pricing exceeds historical thresholds.")
            
        st.info(f"💡 **AI Suggestion:** A {profit_pct-2}% margin would increase win chance by ~11%.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 5. ACTION FOOTER ---
    st.markdown("<br>", unsafe_allow_html=True)
    _, f2, f3 = st.columns([3, 1, 1])
    with f2:
        if st.button("💾 Save Draft", use_container_width=True):
            st.toast("Bid saved to Supabase")
    with f3:
        if st.button("🚀 Push Proposal", type="primary", use_container_width=True):
            st.balloons()

if __name__ == "__main__":
    bid_generation_page()