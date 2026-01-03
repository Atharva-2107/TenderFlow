# import streamlit as st
# import pandas as pd
# import numpy as np
# import plotly.graph_objects as go
# import time

# def bid_generation_page():
#     # --- 1. PREMIUM STYLING ---
#     st.markdown("""
#         <style>
#         @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
#         .main-title {
#             font-family: 'Inter', sans-serif;
#             font-size: 2.6rem;
#             font-weight: 800;
#             color: #64748B;
#             letter-spacing: -0.025em;
#             margin-bottom: 0.2rem;
#         }
#         .section-header {
#             font-family: 'Inter', sans-serif;
#             font-size: 1.25rem;
#             font-weight: 600;
#             color: #64748B;
#             margin-top: 2rem;
#             margin-bottom: 1rem;
#             display: flex;
#             align-items: center;
#         }
#         .bid-amount-box {
#             background: linear-gradient(135deg, #10B981 0%, #059669 100%);
#             padding: 2.5rem;
#             border-radius: 20px;
#             color: white;
#             text-align: center;
#             box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.2);
#         }
#         .price-text {
#             font-size: 3.5rem;
#             font-weight: 800;
#             margin: 0.5rem 0;
#         }
#         /* Style for the AI status badge */
#         .ai-badge {
#             background-color: #E0F2FE;
#             color: #0369A1;
#             padding: 4px 12px;
#             border-radius: 9999px;
#             font-size: 0.75rem;
#             font-weight: 600;
#             text-transform: uppercase;
#         }
#         </style>
#     """, unsafe_allow_html=True)

#     # --- 2. HEADER ---
#     st.markdown('<div class="main-title">💎 Bid Optimization Dashboard</div>', unsafe_allow_html=True)
#     st.markdown("<p style='color: #64748B; font-size: 1.1rem;'>Integrated Generation, Analysis, and AI Win Prediction.</p>", unsafe_allow_html=True)

#     # --- 3. STEP 1: DOCUMENT UPLOAD ---
#     st.markdown('<div class="section-header">📂 1. Technical Tender Intake</div>', unsafe_allow_html=True)
    
#     with st.container():
#         uploaded_tender = st.file_uploader(
#             "Upload your prepared Technical Proposal/Tender (PDF)", 
#             type=['pdf'],
#             help="Our LlamaParse engine will extract scope items, man-hours, and complexity from this document."
#         )

#     if not uploaded_tender:
#         st.info("💡 **Getting Started:** Upload your technical document above. TenderFlow will analyze the scope and suggest an optimized bid amount.")
#         st.image("https://img.freepik.com/free-vector/data-extraction-concept-illustration_114360-4866.jpg", width=400)
#         return

#     # --- 4. STEP 2: SCOPE EXTRACTION (SIMULATED) ---
#     if 'extraction_done' not in st.session_state:
#         with st.status("🚀 Processing Technical Document...", expanded=True) as status:
#             st.write("Extracting tabular data via LlamaParse...")
#             time.sleep(1.2)
#             st.write("Identifying core deliverables and resource requirements...")
#             time.sleep(1.0)
#             st.write("Mapping technical complexity to historical market benchmarks...")
#             status.update(label="Extraction Complete!", state="complete", expanded=False)
#         st.session_state.extraction_done = True

#     st.divider()

#     # --- 5. MAIN CALCULATION WORKSPACE ---
#     col_left, col_right = st.columns([1.3, 1], gap="large")

#     with col_left:
#         st.markdown('<div class="section-header">🧮 2. Bid Generation & Costing</div>', unsafe_allow_html=True)
#         st.write("Refine extracted scope items and unit costs.")

#         if 'cost_data' not in st.session_state:
#             st.session_state.cost_data = [
#                 {"item": "Technical Design & Architecture", "unit": "Hours", "qty": 180, "base_cost": 85},
#                 {"item": "Core System Development", "unit": "Hours", "qty": 650, "base_cost": 70},
#                 {"item": "Quality Assurance & Testing", "unit": "Lump Sum", "qty": 1, "base_cost": 12000},
#                 {"item": "Deployment & Cloud Provisioning", "unit": "Lump Sum", "qty": 1, "base_cost": 8500},
#             ]

#         total_direct_costs = 0
#         with st.container():
#             for i, row in enumerate(st.session_state.cost_data):
#                 with st.expander(f"📍 {row['item']}", expanded=True):
#                     c1, c2, c3 = st.columns([2, 1, 1])
#                     unit_cost = c1.number_input(f"Unit Cost ({row['unit']})", value=float(row['base_cost']), key=f"cost_{i}")
#                     quantity = c2.number_input(f"Quantity", value=float(row['qty']), key=f"qty_{i}")
#                     subtotal = unit_cost * quantity
#                     c3.markdown(f"<br>**Subtotal:**<br>${subtotal:,.2f}", unsafe_allow_html=True)
#                     total_direct_costs += subtotal

#         st.markdown('<div class="section-header">📊 3. Bid Analysis & Strategy</div>', unsafe_allow_html=True)
#         with st.container():
#             col_s1, col_s2 = st.columns(2)
#             overhead_pct = col_s1.slider("Overhead Recovery (%)", 0, 30, 15, help="Operational costs beyond direct labor.")
#             profit_margin = col_s2.select_slider(
#                 "Target Profit Margin (%)", 
#                 options=[0, 5, 8, 10, 12, 15, 18, 20, 25, 30], 
#                 value=12
#             )
            
#             # THE BID CALCULATION
#             overhead_amt = total_direct_costs * (overhead_pct / 100)
#             base_total = total_direct_costs + overhead_amt
#             final_bid_amount = base_total * (1 + (profit_margin / 100))

#     with col_right:
#         st.markdown('<div class="section-header">🤖 4. AI Win Prediction <span class="ai-badge" style="margin-left:10px;">XGBoost Ready</span></div>', unsafe_allow_html=True)
        
#         # Suggested Bid Box
#         st.markdown(f"""
#             <div class="bid-amount-box">
#                 <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; font-weight: 600;">Proposed Bid Amount</div>
#                 <div class="price-text">${final_bid_amount:,.2f}</div>
#                 <div style="font-size: 0.85rem; opacity: 0.8;">Includes {profit_margin}% Margin & {overhead_pct}% Overheads</div>
#             </div>
#         """, unsafe_allow_html=True)

#         st.write("")

#         # XGBoost Win Probability Logic
#         # 1. INTEGRATION HOOK: In production, you would use:
#         # payload = {"bid_amount": final_bid_amount, "margin": profit_margin, "complexity": 0.8}
#         # response = requests.post("http://localhost:8000/predict-win", json=payload)
#         # win_prob = response.json()['probability']
        
#         # 2. CURRENT DYNAMIC PLACEHOLDER:
#         # Market Cap simulation - probability drops sharply as bid approaches 1.2M
#         market_cap = 1100000 
#         ratio = final_bid_amount / market_cap
        
#         # Non-linear probability curve (simulating AI behavior)
#         # Prob increases with efficiency but drops with high pricing
#         win_prob = np.exp(-2.5 * (ratio - 0.7)**2) 
#         win_prob = np.clip(win_prob, 0.05, 0.95)

#         fig = go.Figure(go.Indicator(
#             mode = "gauge+number",
#             value = win_prob * 100,
#             title = {'text': "AI Win Confidence", 'font': {'size': 18, 'color': '#64748B'}},
#             gauge = {
#                 'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#cbd5e1"},
#                 'bar': {'color': "#10B981"},
#                 'bgcolor': "white",
#                 'borderwidth': 2,
#                 'bordercolor': "#e2e8f0",
#                 'steps': [
#                     {'range': [0, 40], 'color': '#fee2e2'},
#                     {'range': [40, 70], 'color': '#fef3c7'},
#                     {'range': [70, 100], 'color': '#d1fae5'}],
#             }
#         ))
#         fig.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
#         st.plotly_chart(fig, use_container_width=True)

#         with st.container():
#             st.markdown("#### Strategic Insights")
            
#             # Show Projected Profit
#             projected_profit = final_bid_amount - base_total
#             st.write(f"💵 **Projected Profit:** ${projected_profit:,.2f}")

#             if win_prob > 0.75:
#                 st.success("✅ **Strong Positioning:** Your pricing is optimized for the current market saturation.")
#             elif win_prob > 0.40:
#                 st.warning("⚖️ **Competitive Baseline:** You are in the standard bidding range. Technical score will be the tie-breaker.")
#             else:
#                 st.error("🚨 **Low Probability:** Pricing exceeds historical thresholds. Consider reducing overhead recovery.")

#             st.info(f"💡 **AI Suggestion:** A **{profit_margin-2}%** margin would move your win chance to **{(win_prob+0.12)*100:.0f}%**.")

#     # --- 6. ACTION FOOTER ---
#     st.divider()
#     f1, f2, f3 = st.columns([2, 1, 1])
#     with f1:
#         st.write("🔒 *Calculations stored in your private Supabase instance.*")
#     with f2:
#         if st.button("💾 Save to Dashboard", use_container_width=True):
#             st.toast("Bid saved successfully!")
#     with f3:
#         if st.button("🚀 Apply for Tender", type="primary", use_container_width=True):
#             st.balloons()
#             st.success("Bid Finalized! Redirecting to submission portal...")

# if __name__ == "__main__":
#     bid_generation_page()

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

def calculate_ai_confidence(final_bid, prime_cost, overhead, profit):
    """
    Simulates a multi-factor AI scoring engine.
    In production, this would be a call to your FastAPI /predict-win endpoint.
    """
    # Factor 1: Market Benchmark (Simulated historical data)
    market_benchmark = 78000 
    price_score = np.exp(-2.8 * (final_bid / market_benchmark - 0.75)**2)
    
    # Factor 2: Efficiency Score (Ratio of Overhead vs Prime)
    # High overheads usually lower win confidence in technical tenders
    efficiency_score = 1.0 - (overhead / 40) 
    
    # Factor 3: Margin Health
    # Extremely low margins look suspicious/risky; extremely high look greedy
    margin_score = np.clip(1 - abs(profit - 15)/30, 0, 1)
    
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
    # This section shows ONLY when no file has been processed yet
    if 'extraction_done' not in st.session_state:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Centering the uploader for a professional landing-page feel
        _, col_mid, _ = st.columns([1, 2, 1]) 
        
        with col_mid:
            st.markdown('<div class="glass-card" style="text-align: center;">', unsafe_allow_html=True)
            st.markdown("### 📂 Initialize New Bid")
            st.write("Upload your technical proposal to begin AI cost extraction.")
            
            # THE PDF UPLOAD WIDGET
            uploaded_tender = st.file_uploader("Drop PDF here", type=['pdf'], label_visibility="collapsed")
            
            if uploaded_tender:
                with st.status("🔮 Analyzing with Llama-3.3...", expanded=True):
                    # This is where your FastAPI call will go tomorrow
                    time.sleep(1.5) 
                    st.session_state.extraction_done = True
                    st.rerun() # Refresh page to show the Dashboard
            st.markdown('</div>', unsafe_allow_html=True)
        return # Prevents the rest of the dashboard from showing until upload is done

    # --- 4. DASHBOARD VIEW ---
    st.divider()
    left_col, right_col = st.columns([1.8, 1.2], gap="large")

    with left_col:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="label-text">Resource Ledger</p>', unsafe_allow_html=True)
        
        if 'cost_df' not in st.session_state:
            st.session_state.cost_df = pd.DataFrame([
                {"Task": "Core Backend Architecture", "Qty": 180, "Rate": 95},
                {"Task": "Frontend UI/UX Implementation", "Qty": 320, "Rate": 75},
                {"Task": "API Integration & Testing", "Qty": 140, "Rate": 85},
            ])

        edited_df = st.data_editor(
            st.session_state.cost_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Rate": st.column_config.NumberColumn(format="$%d"),
                "Qty": st.column_config.NumberColumn(step=1),
            }
        )
        total_prime = (edited_df['Qty'] * edited_df['Rate']).sum()
        st.markdown(f"<div style='text-align: right; color: #A855F7; font-family: JetBrains Mono; font-size: 1.2rem;'>Prime Cost: ${total_prime:,.2f}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="label-text">Pricing Strategy</p>', unsafe_allow_html=True)
        c_s1, c_s2 = st.columns(2)
        overhead_pct = c_s1.slider("Overhead Recovery (%)", 0, 30, 12)
        profit_pct = c_s2.select_slider("Target Profit (%)", options=[5, 10, 15, 20, 25, 30], value=15)
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        # FINAL PROPOSAL CALCULATION
        base_total = total_prime * (1 + (overhead_pct / 100))
        final_bid = base_total * (1 + (profit_pct / 100))
        
        st.markdown(f"""
            <div class="bid-box">
                <div class="label-text" style="color: #DDD6FE;">Final Optimized Bid</div>
                <div class="bid-price">${final_bid:,.2f}</div>
                <div style="font-size: 0.85rem; color: #C4B5FD; opacity: 0.9;">
                    Gross Profit: ${(final_bid - total_prime):,.2f}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        # AI WIN CONFIDENCE LOGIC
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="label-text">AI Win Confidence</p>', unsafe_allow_html=True)
        
        # Calling our new logic function
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