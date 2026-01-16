import streamlit as st
import plotly.graph_objects as go
import random
import sys
from pathlib import Path
import base64
import os

# Ensure project root is in sys.path FIRST
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Correct import because utils is inside frontend
from frontend.utils.auth import can_access
from backend.risk_engine import analyze_pdf

def get_base64_of_bin_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# ACCESS CONTROL
if not can_access("risk_analysis"):
    st.error("You are not authorized to access this page.")
    st.stop()

# SESSION STATE
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "last_file_id" not in st.session_state:
    st.session_state.last_file_id = None

def risk_analysis_page():
    # STYLING ENGINE
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
        
        :root {
            --primary: #a855f7;
            --bg-gradient: radial-gradient(circle at 20% 30%, #1a1c4b 0%, #0f111a 100%);
        }

        .stApp {
            background: var(--bg-gradient) !important;
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #ffffff;
        }
                
        header, footer { visibility: hidden; }
                
        .block-container{
            margin-top: -70px;        
        }

        /* Modern Top Nav */
        header[data-testid="stHeader"] {
            background: rgba(15, 17, 26, 0.8) !important;
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(168, 85, 247, 0.2);
        }

        /* Glassmorphism Cards */
        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }

        .glass-card:hover {
            border: 1px solid rgba(168, 85, 247, 0.4);
            background: rgba(255, 255, 255, 0.05);
            transform: translateY(-2px);
        }

        /* Typography */
        .hero-title {
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(to right, #ffffff, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }

        .hero-sub {
            color: rgba(255,255,255,0.6);
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }

        /* Risk Tags */
        .risk-tag {
            padding: 4px 12px;
            border-radius: 99px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: inline-block;
            margin-bottom: 12px;
            border: 1px solid rgba(255,255,255,0.2);
        }

        .tag-critical { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border-color: #ef4444; }
        .tag-warning { background: rgba(245, 158, 11, 0.2); color: #fcd34d; border-color: #f59e0b; }
        
        /* Category Badges */
        .cat-badge {
            color: #a855f7;
            font-weight: 600;
            font-size: 0.85rem;
        }

        /* Custom File Uploader Style */
        [data-testid="stFileUploader"] {
            background: rgba(168, 85, 247, 0.05);
            border: 2px dashed rgba(168, 85, 247, 0.3);
            border-radius: 15px;
            padding: 20px;
        }

        /* Metric Styling */
        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.02);
            padding: 15px;
            border-radius: 12px;
            border-left: 3px solid #a855f7;
        }
        </style>
    """, unsafe_allow_html=True)

    # 1. NAVIGATION BAR
    nav_col1, nav_col2 = st.columns([2, 1])
    with nav_col1:
        logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
        logo = get_base64_of_bin_file(logo_path)
        if logo:
            st.markdown(f'<img src="data:image/png;base64,{logo}" width="200" style="margin-top:5px;">', unsafe_allow_html=True)

    with nav_col2:
            header_cols = st.columns([3, 3, 3, 3, 3, 3])
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
                # else:
                #     st.button("⬈", key="h_risk_disabled", disabled=True)
                # h_cols = st.columns(6)
                # pages = [("⊞", "app.py", "help= "), ("⎘", "pages/tenderGeneration.py"), ("◈", "pages/tenderAnalyser.py"), 
                #          ("✦", "pages/bidGeneration.py"), ("⬈", "pages/riskAnalysis.py")]
                # for i, (icon, path) in enumerate(pages):
                #     with h_cols[i+1]:
                #         if st.button(icon, key=f"nav_{i}"):
                #             st.switch_page(path)

    st.markdown("<div> <hr> </div>", unsafe_allow_html=True)
    # 2. HERO SECTION
    # st.markdown('<div style="height: 40px;"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="hero-title">Risk Intelligence</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Deep Neural Analysis of Contractual Obligations & Financial Exposure.</p>', unsafe_allow_html=True)

    # 3. UPLOAD ZONE
    uploaded_file = st.file_uploader("", type=["pdf"])

    if uploaded_file:
        file_id = (uploaded_file.name, uploaded_file.size)
        if st.session_state.last_file_id != file_id:
            with st.status("🧬 Scanning Document Vectors...", expanded=True) as status:
                st.session_state.analysis_results = analyze_pdf(uploaded_file)
                st.session_state.last_file_id = file_id
                status.update(label="Analysis Verified", state="complete")

    st.markdown('<hr style="border-color: rgba(168, 85, 247, 0.2); margin: 30px 0; margin-top: -20px;">', unsafe_allow_html=True)

    # 4. MAIN DASHBOARD AREA
    if st.session_state.analysis_results:
        # Sidebar Filter Styling
        with st.sidebar:
            st.markdown("### 🎚️ Analysis Tuning")
            appetite = st.slider("Sensitivity Threshold", 0, 100, 20)
            focus_cats = st.multiselect("Active Dimensions", 
                                      ['Financial', 'Timeline', 'Legal', 'Payment', 'Resource'],
                                      default=['Financial', 'Timeline', 'Legal', 'Payment', 'Resource'])
            if st.button("Reset Session", use_container_width=True):
                st.session_state.analysis_results = None
                st.rerun()

        filtered_data = [r for r in st.session_state.analysis_results if r["severity"] >= appetite and r["category"] in focus_cats]

        # Top Insights Row
        col_viz, col_met = st.columns([1.5, 1])
        
        with col_viz:
            cats = ['Financial', 'Timeline', 'Legal', 'Payment', 'Resource']
            vals = [sum([r["severity"] for r in st.session_state.analysis_results if r["category"] == c]) / 
                    max(len([r for r in st.session_state.analysis_results if r["category"] == c]), 1) for c in cats]
            
            fig = go.Figure(go.Scatterpolar(r=vals, theta=cats, fill='toself', 
                                            fillcolor='rgba(168, 85, 247, 0.2)',
                                            line=dict(color='#a855f7', width=2)))
            fig.update_layout(
                polar=dict(bgcolor='rgba(0,0,0,0)', radialaxis=dict(visible=True, gridcolor='rgba(255,255,255,0.1)', color="#fff")),
                paper_bgcolor='rgba(0,0,0,0)', showlegend=False, height=350, margin=dict(t=40, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_met:
            critical_count = len([r for r in filtered_data if r["status"] == "Critical"])
            st.metric("Risk Vectors", f"{len(filtered_data)}", f"{critical_count} Critical")
            
            st.markdown('<div style="margin-top:20px;"></div>', unsafe_allow_html=True)
            if critical_count > 0:
                st.markdown(f"""
                    <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; padding: 15px; border-radius: 12px;">
                        <span style="color: #ef4444; font-weight: 700;">⚠️ URGENT ATTENTION</span><br>
                        <small style="color: #fca5a5;">High-severity clauses detected in {filtered_data[0]['category']}.</small>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.success("Document meets safety thresholds.")

        # 5. CLAUSE FEED
        st.markdown("### 🔍 Vulnerability Feed")
        for r in filtered_data:
            tag_class = "tag-critical" if r["status"] == "Critical" else "tag-warning"
            
            st.markdown(f"""
                <div class="glass-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <span class="risk-tag {tag_class}">{r['status']}</span>
                        <span class="cat-badge">{r['category']}</span>
                    </div>
                    <h4 style="margin: 10px 0; color: #ffffff;">{r['clause']}</h4>
                    <p style="color: rgba(255,255,255,0.5); font-style: italic; font-size: 0.9rem; border-left: 2px solid #a855f7; padding-left: 15px;">
                        "{r['content']}"
                    </p>
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.05);">
                        <strong style="color: #a855f7;">AI Impact Analysis:</strong>
                        <p style="margin-top: 5px; color: #cbd5e1;">{r['impact']}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="text-align: center; padding: 100px 20px; border: 1px solid rgba(255,255,255,0.05); border-radius: 30px;">
                <h3 style="color: rgba(255,255,255,0.2);">Awaiting Document Upload</h3>
                <p style="color: rgba(255,255,255,0.1);">Drag and drop a PDF to begin the risk vectoring process.</p>
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    risk_analysis_page()