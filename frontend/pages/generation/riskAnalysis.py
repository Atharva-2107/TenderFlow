import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random

def risk_analysis_page():
    # --- 1. ENHANCED STYLING ---
    st.markdown("""
        <style>
        .risk-header { font-size: 2.2rem; font-weight: 700; color: #64748B; }
        .risk-tag {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 8px;
        }
        .tag-financial { background-color: #fee2e2; color: #991b1b; }
        .tag-legal { background-color: #e0f2fe; color: #075985; }
        .tag-ops { background-color: #fef3c7; color: #92400e; }
        .tag-payment { background-color: #f3e8ff; color: #6b21a8; }
        
        .risk-card {
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.2rem;
            border: 1px solid #e2e8f0;
            background-color: white;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }
        .risk-card:hover { transform: translateY(-2px); }
        .border-red { border-left: 6px solid #ef4444; }
        .border-amber { border-left: 6px solid #f59e0b; }
        .border-green { border-left: 6px solid #22c55e; }
        </style>
    """, unsafe_allow_html=True)

    # --- 2. DATA SIMULATION LOGIC (REPLACES HARDCODED LISTS) ---
    def simulate_analysis(filename):
        """Simulates the Gemini/LlamaParse output for different documents"""
        categories = ['Financial', 'Timeline', 'Legal', 'Payment', 'Resource']
        clauses = [
            ("Liquidated Damages", "Financial", "Penalty of X% per day of delay."),
            ("Indemnity", "Legal", "Contractor liable for all indirect losses."),
            ("Payment Terms", "Payment", "Net 60/90 day payment cycles."),
            ("Force Majeure", "Legal", "Limited definition of excusable delays."),
            ("Termination", "Legal", "Issuer can terminate for convenience without fee."),
            ("Mobilization", "Timeline", "Start date within 48 hours of award."),
            ("Retentions", "Financial", "10% retention held until 12 months post-completion."),
            ("Price Escalation", "Financial", "No adjustments allowed for fuel/material spikes.")
        ]
        
        results = []
        for name, cat, desc in clauses:
            severity = random.randint(20, 95)
            status = "Critical" if severity > 75 else "Warning" if severity > 45 else "Low"
            results.append({
                "category": cat,
                "clause": name,
                "content": desc,
                "severity": severity,
                "status": status,
                "impact": f"AI calculates a {severity}/100 impact score based on sector standards.",
                "tag_class": f"tag-{cat.lower()}"
            })
        return results

    # Initialize Session State for dynamic data
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None

    # --- 3. HEADER & UPLOAD ---
    st.markdown('<div class="risk-header">🕵️ Contractual Risk Intelligence</div>', unsafe_allow_html=True)
    st.write("AI-driven deep scan of Tender Documents for predatory clauses and hidden liabilities.")

    uploaded_file = st.file_uploader("Upload Tender RFP or Contract Draft", type=['pdf'])
    
    if uploaded_file and st.session_state.analysis_results is None:
        with st.status("LlamaParse & Gemini Analyzing Document...", expanded=True) as status:
            st.write("Extracting legal text structures...")
            import time; time.sleep(1.5)
            st.write("Categorizing 5 Pillars of Risk...")
            time.sleep(1)
            st.session_state.analysis_results = simulate_analysis(uploaded_file.name)
            status.update(label="Analysis Complete!", state="complete")

    st.divider()

    if st.session_state.analysis_results:
        # --- 4. SIDEBAR SETTINGS (CONTROLS THE DYNAMICS) ---
        with st.sidebar:
            st.header("⚙️ View Settings")
            appetite = st.slider("Risk Sensitivity Threshold", 0, 100, 40, help="Hide risks with severity below this score.")
            focus_cats = st.multiselect("Filter by Category", 
                                      ['Financial', 'Timeline', 'Legal', 'Payment', 'Resource'], 
                                      default=['Financial', 'Timeline', 'Legal', 'Payment', 'Resource'])
            
            # Reset Button
            if st.button("Clear Analysis"):
                st.session_state.analysis_results = None
                st.rerun()

        # Filtering Logic
        filtered_data = [r for r in st.session_state.analysis_results 
                         if r['severity'] >= appetite and r['category'] in focus_cats]

        # --- 5. DYNAMIC EXECUTIVE SUMMARY ---
        col_chart, col_summary = st.columns([1, 1])

        with col_chart:
            # Calculate dynamic averages for Radar Chart
            radar_cats = ['Financial', 'Timeline', 'Legal', 'Payment', 'Resource']
            radar_vals = []
            for c in radar_cats:
                cat_scores = [r['severity'] for r in st.session_state.analysis_results if r['category'] == c]
                radar_vals.append(sum(cat_scores)/len(cat_scores) if cat_scores else 0)

            fig = go.Figure(data=go.Scatterpolar(
                r=radar_vals, theta=radar_cats, fill='toself', line_color='#ef4444'
            ))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                              showlegend=False, height=350, margin=dict(l=40, r=40, t=40, b=40))
            st.plotly_chart(fig, use_container_width=True)

        with col_summary:
            st.subheader("⚠️ Executive Flag Summary")
            critical_count = len([r for r in filtered_data if r['status'] == "Critical"])
            warning_count = len([r for r in filtered_data if r['status'] == "Warning"])
            
            st.metric("Filtered Critical Risks", critical_count, delta=f"{warning_count} Warnings", delta_color="off")
            
            if critical_count > 0:
                highest_risk = max(filtered_data, key=lambda x: x['severity'])
                st.error(f"**Highest Priority:** {highest_risk['clause']} ({highest_risk['severity']}/100)")
            else:
                st.success("No high-severity risks found with current filters.")

            if st.button("Generate Mitigation Strategy", type="primary"):
                st.write("✨ *Gemini is analyzing negotiation paths for your specific risks...*")

        st.divider()

        # --- 6. DYNAMIC CLAUSE FEED ---
        st.subheader(f"🔍 Clause Breakdown ({len(filtered_data)} active flags)")
        
        if not filtered_data:
            st.info("No clauses match your current filters. Adjust the 'Risk Sensitivity' in the sidebar.")
        else:
            for r in filtered_data:
                border = "border-red" if r['status'] == "Critical" else "border-amber" if r['status'] == "Warning" else "border-green"
                st.markdown(f"""
                    <div class="risk-card {border}">
                        <span class="risk-tag {r['tag_class']}">{r['category']}</span>
                        <h4 style="margin: 5px 0;">{r['clause']} <span style="font-size: 0.8rem; color: #64748b;">(Score: {r['severity']})</span></h4>
                        <p style="font-style: italic; color: #475569; margin-bottom: 10px;">"{r['content']}"</p>
                        <p><strong>AI Analysis:</strong> {r['impact']}</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        # Placeholder when no file is uploaded
        st.info("Please upload a contract or RFP document above to begin the risk analysis.")

if __name__ == "__main__":
    risk_analysis_page()