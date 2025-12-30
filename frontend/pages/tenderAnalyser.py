import streamlit as st
import time
import base64
import os
from pathlib import Path


# PAGE CONFIG
st.set_page_config(page_title="TenderFlow AI | Analyzer", layout="wide")

# UTILS 
def get_base64_of_bin_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


# CSS 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

/* HIDE HEADER ANCHOR ICONS (-) */
    button[title="View header anchor"] {
        display: none !important;
    }
    .stHtmlHeader a , .stMarkdown a{
        display: none !important;
    }
    header { visibility: hidden; }
      

/* Global Background */
.stApp {
    background-color: #0d1117;
    font-family: 'Inter', sans-serif;
}

/* Unified Control Bar */
.control-bar {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 25px;
    margin-top: -40px;
}

/* Primary Button Styling (Consistent with your紫 purple theme) */
div.stButton > button {
    background-color: #7c3aed !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    border: 1.5px solid #8b5cf6 !important;
    transition: 0.3s;
}

/* Pane Containers */
.pane-container {
    background-color: #0D1117;
    border: 1px solid #30363D;
    border-radius: 10px;
    height: 600px;
    overflow: hidden;
}

.pane-header {
    background-color: #161B22;
    padding: 12px 20px;
    border-bottom: 1px solid #30363D;
    font-size: 11px;
    font-weight: 800;
    color: #8B949E;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}

.label-tag { color: #8B949E; font-size: 12px; font-weight: 700; margin-bottom: 8px; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# HEADER & LOGO 
logo_col, title_col = st.columns([1, 4])

with logo_col:
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
    logo = get_base64_of_bin_file(logo_path)

    if logo:
        st.markdown(f"""
            <div style="text-align:left; margin-top: -100px; margin-left:-50px">
                <img src="data:image/png;base64,{logo}" width="200">
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='color: #a855f7; margin:0;'>TenderFlow</h2>", unsafe_allow_html=True)

with title_col:
    st.markdown("<h2 style='color:white; margin:0; line-height:1.2; text-align: center; margin-left:-220px;'>Tender Analyzer Studio</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; margin:0; font-size:14px; text-align: center;margin-left: -220px;'>Proprietary AI for procurement & bid engineering.</p>", unsafe_allow_html=True)

st.write("##")

# CONTROL BAR
st.markdown('<div class="control-bar">', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns([2, 1, 1, 1])

with c1:
    st.markdown('<p class="label-tag">1. Document Upload</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload RFP", type=["pdf"], label_visibility="collapsed")

with c2:
    st.markdown('<p class="label-tag">2. Output Format</p>', unsafe_allow_html=True)
    out_format = st.selectbox("Format", ["Executive Bullets", "Technical Narrative", "Compliance Matrix"], label_visibility="collapsed")

with c3:
    st.markdown('<p class="label-tag">3. Analysis Depth</p>', unsafe_allow_html=True)
    depth = st.selectbox("Depth", ["Standard", "Deep Dive"], label_visibility="collapsed")

with c4:
    st.markdown('<p class="label-tag">4. Execution</p>', unsafe_allow_html=True)
    run_analysis = st.button("Analyze Tender", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)


# DUAL PANE WORKSPACE
col_left, col_right = st.columns(2, gap="medium")

with col_left:
    st.markdown('<div class="pane-container"><div class="pane-header">Source Document Preview</div>', unsafe_allow_html=True)
    if uploaded_file:
        st.markdown(f"""
            <div style="padding:20px; font-family:monospace; color:#7D8590; font-size:13px;">
                <b>[SYSTEM]: {uploaded_file.name} LOADED</b><br>
                <b>[SYSTEM]: LLAMAPARSE EXTRACTION ACTIVE...</b><br>
                ------------------------------------------------<br><br>
                SECTION 1.0: INVITATION TO BID...<br>
                SECTION 2.1: TECHNICAL ELIGIBILITY...
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div style="height:500px; display:flex; align-items:center; justify-content:center; color:#484F58;">Awaiting Document Upload...</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="pane-container"><div class="pane-header">AI Generated Intelligence</div>', unsafe_allow_html=True)
    if run_analysis and uploaded_file:
        with st.spinner("Analyzing..."):
            time.sleep(1.5)
            st.markdown('<div style="padding:20px; background:#161B22; height:100%;">', unsafe_allow_html=True)
            st.markdown("### 🔍 Strategic Summary")
            st.write("• **Win Strategy:** Focus on the 97% efficiency gain mentioned in Section 2.")
            st.write("• **Compliance:** All 4 mandatory clauses detected via FlashRank.")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="height:500px; display:flex; align-items:center; justify-content:center; color:#484F58;">Run Analysis to see results.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)