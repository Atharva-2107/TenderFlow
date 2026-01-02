import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time

def bid_generation_page():
    # --- 1. PREMIUM STYLING ---
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        .main-title {
            font-family: 'Inter', sans-serif;
            font-size: 2.6rem;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.025em;
            margin-bottom: 0.2rem;
        }
        .section-header {
            font-family: 'Inter', sans-serif;
            font-size: 1.25rem;
            font-weight: 600;
            color: #1E293B;
            margin-top: 2rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
        }
        .bid-amount-box {
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            padding: 2.5rem;
            border-radius: 20px;
            color: white;
            text-align: center;
            box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.2);
        }
        .price-text {
            font-size: 3.5rem;
            font-weight: 800;
            margin: 0.5rem 0;
        }
        /* Style for the AI status badge */
        .ai-badge {
            background-color: #E0F2FE;
            color: #0369A1;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- 2. HEADER ---
    st.markdown('<div class="main-title">💎 Bid Optimization Dashboard</div>', unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B; font-size: 1.1rem;'>Integrated Generation, Analysis, and AI Win Prediction.</p>", unsafe_allow_html=True)

    # --- 3. STEP 1: DOCUMENT UPLOAD ---
    st.markdown('<div class="section-header">📂 1. Technical Tender Intake</div>', unsafe_allow_html=True)
    
    with st.container():
        uploaded_tender = st.file_uploader(
            "Upload your prepared Technical Proposal/Tender (PDF)", 
            type=['pdf'],
            help="Our LlamaParse engine will extract scope items, man-hours, and complexity from this document."
        )

    if not uploaded_tender:
        st.info("💡 **Getting Started:** Upload your technical document above. TenderFlow will analyze the scope and suggest an optimized bid amount.")
        st.image("https://img.freepik.com/free-vector/data-extraction-concept-illustration_114360-4866.jpg", width=400)
        return

    # --- 4. STEP 2: SCOPE EXTRACTION (SIMULATED) ---
    if 'extraction_done' not in st.session_state:
        with st.status("🚀 Processing Technical Document...", expanded=True) as status:
            st.write("Extracting tabular data via LlamaParse...")
            time.sleep(1.2)
            st.write("Identifying core deliverables and resource requirements...")
            time.sleep(1.0)
            st.write("Mapping technical complexity to historical market benchmarks...")
            status.update(label="Extraction Complete!", state="complete", expanded=False)
        st.session_state.extraction_done = True

    st.divider()

    # --- 5. MAIN CALCULATION WORKSPACE ---
    col_left, col_right = st.columns([1.3, 1], gap="large")

    with col_left:
        st.markdown('<div class="section-header">🧮 2. Bid Generation & Costing</div>', unsafe_allow_html=True)
        st.write("Refine extracted scope items and unit costs.")

        if 'cost_data' not in st.session_state:
            st.session_state.cost_data = [
                {"item": "Technical Design & Architecture", "unit": "Hours", "qty": 180, "base_cost": 85},
                {"item": "Core System Development", "unit": "Hours", "qty": 650, "base_cost": 70},
                {"item": "Quality Assurance & Testing", "unit": "Lump Sum", "qty": 1, "base_cost": 12000},
                {"item": "Deployment & Cloud Provisioning", "unit": "Lump Sum", "qty": 1, "base_cost": 8500},
            ]

        total_direct_costs = 0
        with st.container():
            for i, row in enumerate(st.session_state.cost_data):
                with st.expander(f"📍 {row['item']}", expanded=True):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    unit_cost = c1.number_input(f"Unit Cost ({row['unit']})", value=float(row['base_cost']), key=f"cost_{i}")
                    quantity = c2.number_input(f"Quantity", value=float(row['qty']), key=f"qty_{i}")
                    subtotal = unit_cost * quantity
                    c3.markdown(f"<br>**Subtotal:**<br>${subtotal:,.2f}", unsafe_allow_html=True)
                    total_direct_costs += subtotal

        st.markdown('<div class="section-header">📊 3. Bid Analysis & Strategy</div>', unsafe_allow_html=True)
        with st.container():
            col_s1, col_s2 = st.columns(2)
            overhead_pct = col_s1.slider("Overhead Recovery (%)", 0, 30, 15, help="Operational costs beyond direct labor.")
            profit_margin = col_s2.select_slider(
                "Target Profit Margin (%)", 
                options=[0, 5, 8, 10, 12, 15, 18, 20, 25, 30], 
                value=12
            )
            
            # THE BID CALCULATION
            overhead_amt = total_direct_costs * (overhead_pct / 100)
            base_total = total_direct_costs + overhead_amt
            final_bid_amount = base_total * (1 + (profit_margin / 100))

    with col_right:
        st.markdown('<div class="section-header">🤖 4. AI Win Prediction <span class="ai-badge" style="margin-left:10px;">XGBoost Ready</span></div>', unsafe_allow_html=True)
        
        # Suggested Bid Box
        st.markdown(f"""
            <div class="bid-amount-box">
                <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; font-weight: 600;">Proposed Bid Amount</div>
                <div class="price-text">${final_bid_amount:,.2f}</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">Includes {profit_margin}% Margin & {overhead_pct}% Overheads</div>
            </div>
        """, unsafe_allow_html=True)

        st.write("")

        # XGBoost Win Probability Logic
        # 1. INTEGRATION HOOK: In production, you would use:
        # payload = {"bid_amount": final_bid_amount, "margin": profit_margin, "complexity": 0.8}
        # response = requests.post("http://localhost:8000/predict-win", json=payload)
        # win_prob = response.json()['probability']
        
        # 2. CURRENT DYNAMIC PLACEHOLDER:
        # Market Cap simulation - probability drops sharply as bid approaches 1.2M
        market_cap = 1100000 
        ratio = final_bid_amount / market_cap
        
        # Non-linear probability curve (simulating AI behavior)
        # Prob increases with efficiency but drops with high pricing
        win_prob = np.exp(-2.5 * (ratio - 0.7)**2) 
        win_prob = np.clip(win_prob, 0.05, 0.95)

        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = win_prob * 100,
            title = {'text': "AI Win Confidence", 'font': {'size': 18, 'color': '#64748B'}},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#cbd5e1"},
                'bar': {'color': "#10B981"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "#e2e8f0",
                'steps': [
                    {'range': [0, 40], 'color': '#fee2e2'},
                    {'range': [40, 70], 'color': '#fef3c7'},
                    {'range': [70, 100], 'color': '#d1fae5'}],
            }
        ))
        fig.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

        with st.container():
            st.markdown("#### Strategic Insights")
            
            # Show Projected Profit
            projected_profit = final_bid_amount - base_total
            st.write(f"💵 **Projected Profit:** ${projected_profit:,.2f}")

            if win_prob > 0.75:
                st.success("✅ **Strong Positioning:** Your pricing is optimized for the current market saturation.")
            elif win_prob > 0.40:
                st.warning("⚖️ **Competitive Baseline:** You are in the standard bidding range. Technical score will be the tie-breaker.")
            else:
                st.error("🚨 **Low Probability:** Pricing exceeds historical thresholds. Consider reducing overhead recovery.")

            st.info(f"💡 **AI Suggestion:** A **{profit_margin-2}%** margin would move your win chance to **{(win_prob+0.12)*100:.0f}%**.")

    # --- 6. ACTION FOOTER ---
    st.divider()
    f1, f2, f3 = st.columns([2, 1, 1])
    with f1:
        st.write("🔒 *Calculations stored in your private Supabase instance.*")
    with f2:
        if st.button("💾 Save to Dashboard", use_container_width=True):
            st.toast("Bid saved successfully!")
    with f3:
        if st.button("🚀 Apply for Tender", type="primary", use_container_width=True):
            st.balloons()
            st.success("Bid Finalized! Redirecting to submission portal...")

if __name__ == "__main__":
    bid_generation_page()