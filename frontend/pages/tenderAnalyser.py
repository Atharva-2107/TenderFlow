# import streamlit as st
# import time
# import base64
# import os
# import requests  # For FastAPI tomorrow
# from pathlib import Path
# from fpdf import FPDF # Library for the PDF download
# from components.navbar import render_navbar

# # 1. PAGE CONFIG & SESSION STATE
# st.set_page_config(page_title="TenderFlow AI | Analyzer", layout="wide")

# if "summary_result" not in st.session_state:
#     st.session_state.summary_result = None

# # 2. UTILS & HELPER FUNCTIONS
# def get_base64_of_bin_file(path):
#     if os.path.exists(path):
#         with open(path, "rb") as f:
#             return base64.b64encode(f.read()).decode()
#     return None

# def display_pdf_iframe(file_bytes):
#     """Encodes PDF to base64 and displays it in an iframe to avoid component errors."""
#     base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
#     # Using height="100%" to fill the pane container
#     pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="100%" type="application/pdf" style="min-height:560px;"></iframe>'
#     st.markdown(pdf_display, unsafe_allow_html=True)

# # 3. CSS STYLING (From Code 1)
# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

# /* HIDE HEADER ANCHOR ICONS (-) */
#     button[title="View header anchor"] {
#         display: none !important;
#     }
#     .stHtmlHeader a , .stMarkdown a{
#         display: none !important;
#     }
#     header { visibility: hidden; }
      
# /* Global Background */
# .stApp {
#     background-color: #0d1117;
#     font-family: 'Inter', sans-serif;
# }

# /* Unified Control Bar */
# .control-bar {
#     background-color: #161B22;
#     border: 1px solid #30363D;
#     border-radius: 12px;
#     padding: 20px;
#     margin-bottom: 25px;
#     margin-top: -40px;
# }

# /* Primary Button Styling */
# div.stButton > button {
#     background-color: #7c3aed !important;
#     color: white !important;
#     border-radius: 8px !important;
#     font-weight: 600 !important;
#     border: 1.5px solid #8b5cf6 !important;
#     transition: 0.3s;
# }

# /* Pane Containers */
# .pane-container {
#     background-color: #0D1117;
#     border: 1px solid #30363D;
#     border-radius: 10px;
#     height: 600px;
#     overflow: hidden;
#     display: flex;
#     flex-direction: column;
# }

# .pane-header {
#     background-color: #161B22;
#     padding: 12px 20px;
#     border-bottom: 1px solid #30363D;
#     font-size: 11px;
#     font-weight: 800;
#     color: #8B949E;
#     text-transform: uppercase;
#     letter-spacing: 1.2px;
#     flex-shrink: 0; /* Prevent header from shrinking */
# }

# .pane-content {
#     flex-grow: 1;
#     overflow-y: auto; /* Scroll inside the pane if needed */
#     padding: 0;
# }

# .label-tag { color: #8B949E; font-size: 12px; font-weight: 700; margin-bottom: 8px; text-transform: uppercase; }
# </style>
# """, unsafe_allow_html=True)

# # 4. NAVBAR & HEADER
# render_navbar()

# logo_col, title_col = st.columns([1, 4])
# with title_col:
#     st.markdown("<h2 style='color:white; margin:0; line-height:1.2; text-align: center; margin-left:-220px;'>Tender Summarizer Studio</h2>", unsafe_allow_html=True)
#     st.markdown("<p style='color: #94a3b8; margin:0; font-size:14px; text-align: center;margin-left: -220px;'>Proprietary AI for procurement & bid engineering.</p>", unsafe_allow_html=True)

# st.write("##")

# # 5. CONTROL BAR
# st.markdown('<div class="control-bar">', unsafe_allow_html=True)
# c1, c2, c3, c4 = st.columns([2, 1, 1, 1])

# with c1:
#     st.markdown('<p class="label-tag">1. Document Upload</p>', unsafe_allow_html=True)
#     uploaded_file = st.file_uploader("Upload RFP", type=["pdf"], label_visibility="collapsed")

# with c2:
#     st.markdown('<p class="label-tag">2. Output Format</p>', unsafe_allow_html=True)
#     out_format = st.selectbox("Format", ["Executive Bullets", "Technical Narrative", "Compliance Matrix"], label_visibility="collapsed")

# with c3:
#     st.markdown('<p class="label-tag">3. Analysis Depth</p>', unsafe_allow_html=True)
#     depth = st.selectbox("Depth", ["Standard", "Deep Dive"], label_visibility="collapsed")

# with c4:
#     st.markdown('<p class="label-tag">4. Execution</p>', unsafe_allow_html=True)
#     if st.button("Analyze Tender", use_container_width=True):
#         if uploaded_file:
#             with st.spinner("Analyzing..."):
#                 # Simulation for now (Tomorrow we connect to FastAPI here)
#                 time.sleep(1.5)
#                 st.session_state.summary_result = "Strategic Summary: All compliance clauses detected. Win probability increased by focus on Section 2 efficiency gains."
#         else:
#             st.warning("Please upload a file first.")
# st.markdown('</div>', unsafe_allow_html=True)


# # 6. DUAL PANE WORKSPACE
# col_left, col_right = st.columns(2, gap="medium")

# # --- LEFT PANE: PDF PREVIEW ---
# # --- LEFT PANE: PDF PREVIEW ---
# with col_left:
#     # We keep your custom pane-container and header styling
#     st.markdown('<div class="pane-container"><div class="pane-header">Source Document Preview</div>', unsafe_allow_html=True)
    
#     # Create a sub-container for the PDF to control its height precisely
#     pdf_container = st.container()
    
#     with pdf_container:
#         if uploaded_file:
#             # We call the display function here
#             # Note: 550px ensures it fits within your 600px pane-container after the header
#             base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
#             pdf_display = f'''
#                 <iframe 
#                     src="data:application/pdf;base64,{base64_pdf}" 
#                     width="100%" 
#                     height="550px" 
#                     style="border:none; border-radius:0 0 10px 10px;">
#                 </iframe>
#             '''
#             st.markdown(pdf_display, unsafe_allow_html=True)
#         else:
#             # Empty state styling
#             st.markdown('''
#                 <div style="height:550px; display:flex; align-items:center; justify-content:center; color:#484F58; background-color:#0D1117;">
#                     Awaiting Document Upload...
#                 </div>
#             ''', unsafe_allow_html=True)
            
#     st.markdown('</div>', unsafe_allow_html=True)

# # --- RIGHT PANE: ANALYSIS RESULTS ---
# with col_right:
#     st.markdown('<div class="pane-container"><div class="pane-header">AI Generated Intelligence</div><div class="pane-content" style="padding:20px;">', unsafe_allow_html=True)
    
#     if st.session_state.summary_result:
#         # DISPLAY SUMMARY
#         st.markdown(st.session_state.summary_result)
#         st.write("---")
        
#         # GENERATE PDF FOR DOWNLOAD
#         pdf = FPDF()
#         pdf.add_page()
#         pdf.set_font("Arial", size=12)
#         # Simple cleanup to prevent FPDF encoding errors with bold markdown
#         clean_text = st.session_state.summary_result.replace("**", "").replace("##", "")
#         pdf.multi_cell(0, 10, txt=clean_text)
        
#         pdf_bytes = pdf.output(dest='S').encode('latin-1', 'ignore') 
        
#         st.download_button(
#             label="Download Summary as PDF",
#             data=pdf_bytes,
#             file_name="summary.pdf",
#             mime="application/pdf"
#         )
#     else:
#         st.markdown('<div style="height:100%; display:flex; align-items:center; justify-content:center; color:#484F58;">Run Analysis to see results.</div>', unsafe_allow_html=True)
    
#     st.markdown('</div></div>', unsafe_allow_html=True)



import streamlit as st
import time
import base64
import os
import requests  # For FastAPI tomorrow
from pathlib import Path
from fpdf import FPDF # Library for the PDF download
from components.navbar import render_navbar

# 1. PAGE CONFIG & SESSION STATE
st.set_page_config(page_title="TenderFlow AI | Analyzer", layout="wide")

if "summary_result" not in st.session_state:
    st.session_state.summary_result = None

# 2. UTILS & HELPER FUNCTIONS
def get_base64_of_bin_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# 3. CSS STYLING
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

button[title="View header anchor"] { display: none !important; }
.stHtmlHeader a , .stMarkdown a{ display: none !important; }
header { visibility: hidden; }
      
.stApp {
    background-color: #0d1117;
    font-family: 'Inter', sans-serif;
}

.control-bar {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 25px;
    margin-top: -40px;
}

div.stButton > button {
    background-color: #7c3aed !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    border: 1.5px solid #8b5cf6 !important;
    transition: 0.3s;
}

.pane-container {
    background-color: #0D1117;
    border: 1px solid #30363D;
    border-radius: 10px;
    height: 600px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
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

# 4. NAVBAR & HEADER
render_navbar()

logo_col, title_col = st.columns([1, 4])
with title_col:
    st.markdown("<h2 style='color:white; margin:0; line-height:1.2; text-align: center; margin-left:-220px;'>Tender Summarizer Studio</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; margin:0; font-size:14px; text-align: center;margin-left: -220px;'>Proprietary AI for procurement & bid engineering.</p>", unsafe_allow_html=True)

st.write("##")

# 5. CONTROL BAR
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
    if st.button("Analyze Tender", use_container_width=True):
        if uploaded_file:
            with st.spinner("Analyzing..."):
                time.sleep(1.5)
                st.session_state.summary_result = "Strategic Summary: All compliance clauses detected. Win probability increased by focus on Section 2 efficiency gains."
        else:
            st.warning("Please upload a file first.")
st.markdown('</div>', unsafe_allow_html=True)


# 6. DUAL PANE WORKSPACE
col_left, col_right = st.columns(2, gap="medium")

# --- LEFT PANE: PDF PREVIEW ---
with col_left:
    if uploaded_file:
        base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
        # We wrap everything in the pane-container div to lock the styling
        pdf_html = f"""
        <div class="pane-container">
            <div class="pane-header">Source Document Preview</div>
            <iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="100%" style="border:none;"></iframe>
        </div>
        """
        st.markdown(pdf_html, unsafe_allow_html=True)
    else:
        placeholder_left = """
        <div class="pane-container">
            <div class="pane-header">Source Document Preview</div>
            <div style="flex-grow:1; display:flex; align-items:center; justify-content:center; color:#484F58;">
                Awaiting Document Upload...
            </div>
        </div>
        """
        st.markdown(placeholder_left, unsafe_allow_html=True)

# --- RIGHT PANE: AI GENERATED INTELLIGENCE ---
with col_right:
    # We open the main container and header
    st.markdown('<div class="pane-container"><div class="pane-header">AI Generated Intelligence</div>', unsafe_allow_html=True)
    
    # We use a nested area for Streamlit widgets, styled to fill the pane
    content_area = st.container()
    with content_area:
        # This wrapper div ensures padding and scrolling stay inside the black box
        st.markdown('<div style="padding:20px; color:white; height:540px; overflow-y:auto;">', unsafe_allow_html=True)
        
        if st.session_state.summary_result:
            st.markdown(f"### Analysis Result\n{st.session_state.summary_result}")
            st.write("---")
            
            # PDF Generation Logic
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            clean_text = st.session_state.summary_result.replace("**", "").replace("##", "")
            pdf.multi_cell(0, 10, txt=clean_text)
            pdf_bytes = pdf.output(dest='S').encode('latin-1', 'ignore') 
            
            st.download_button(
                label="Download Summary as PDF",
                data=pdf_bytes,
                file_name="summary.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            # Placeholder content when no analysis has run
            st.markdown("""
                <div style="height:100%; display:flex; align-items:center; justify-content:center; color:#484F58; text-align:center;">
                    Run Analysis to see results.
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True) # Close padding/scroll div
    
    st.markdown('</div>', unsafe_allow_html=True) # Close pane-container div

