# import streamlit as st
# import time
# import base64
# import os
# import requests
# from pathlib import Path
# from fpdf import FPDF
# import sys

# # FIX: Add the correct path to find components
# current_dir = os.path.dirname(os.path.abspath(__file__))  # frontend/pages
# parent_dir = os.path.dirname(current_dir)  # frontend/
# sys.path.insert(0, parent_dir)

# # Now import from components
# try:
#     from components.navbar import render_navbar
# except ImportError as e:
#     st.error(f"Import Error: {e}")
#     st.error(f"Current sys.path: {sys.path}")
#     # Define a dummy render_navbar function as fallback
#     def render_navbar():
#         st.markdown("<div style='margin-bottom:20px;'>Navigation placeholder</div>", unsafe_allow_html=True)

# # 1. PAGE CONFIG & SESSION STATE
# st.set_page_config(page_title="TenderFlow AI | Analyzer", layout="wide")

# if "summary_result" not in st.session_state:
#     st.session_state.summary_result = None
# if "pdf_bytes" not in st.session_state:
#     st.session_state.pdf_bytes = None
# if "show_summary" not in st.session_state:
#     st.session_state.show_summary = False
# if "copy_status" not in st.session_state:
#     st.session_state.copy_status = "📋 Copy Summary"
# if "copy_success" not in st.session_state:
#     st.session_state.copy_success = False

# # 2. CSS STYLING
# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

# /* Clean up Streamlit UI */
# button[title="View header anchor"] { display: none !important; }
# .stHtmlHeader a , .stMarkdown a{ display: none !important; }
# header { visibility: hidden; }
      
# .stApp {
#     background-color: #0d1117;
#     font-family: 'Inter', sans-serif;
# }

# /* Control Bar Styling */
# .control-bar {
#     background-color: #161B22;
#     border: 1px solid #30363D;
#     border-radius: 12px;
#     padding: 20px;
#     margin-bottom: 25px;
#     margin-top: -40px;
# }

# /* Button Styling */
# div.stButton > button {
#     background-color: #7c3aed !important;
#     color: white !important;
#     border-radius: 8px !important;
#     font-weight: 600 !important;
#     border: 1.5px solid #8b5cf6 !important;
#     transition: 0.3s;
# }

# /* Clear Results Button Styling */
# .clear-btn {
#     background-color: #30363D !important;
#     color: #c9d1d9 !important;
#     border-radius: 8px !important;
#     font-weight: 600 !important;
#     border: 1px solid #484F58 !important;
#     transition: 0.3s !important;
# }

# .clear-btn:hover {
#     background-color: #484F58 !important;
#     border-color: #8B949E !important;
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
# }

# .label-tag { 
#     color: #8B949E; 
#     font-size: 12px; 
#     font-weight: 700; 
#     margin-bottom: 8px; 
#     text-transform: uppercase; 
# }

# /* Result Scroll Area */
# .content-scroll {
#     padding: 20px; 
#     color: #e6edf3; 
#     height: 540px; 
#     overflow-y: auto;
#     font-size: 15px;
#     line-height: 1.6;
# }

# /* Style for summary content */
# .summary-content {
#     margin-bottom: 20px;
# }

# .summary-title {
#     color: #e6edf3;
#     font-size: 18px;
#     font-weight: 700;
#     margin-bottom: 15px;
#     display: flex;
#     align-items: center;
#     gap: 8px;
# }

# .summary-text {
#     color: #c9d1d9;
#     line-height: 1.6;
#     margin-bottom: 20px;
#     white-space: pre-wrap;
# }

# .divider {
#     border: 0;
#     height: 1px;
#     background: #30363D;
#     margin: 20px 0;
# }

# /* Button alignment container */
# .button-row {
#     display: flex;
#     gap: 15px;
#     margin-top: 20px;
#     width: 100%;
# }

# .button-row > div {
#     flex: 1;
# }

# /* Copy button styling */
# .copy-success {
#     background-color: #238636 !important;
#     color: white !important;
#     border-color: #2ea043 !important;
# }

# /* Fade out animation */
# @keyframes fadeOut {
#     0% { opacity: 1; }
#     70% { opacity: 1; }
#     100% { opacity: 0; }
# }

# .fade-out {
#     animation: fadeOut 2s ease-in-out;
#     animation-fill-mode: forwards;
# }
# </style>
# """, unsafe_allow_html=True)

# # 3. NAVBAR & TITLE
# render_navbar()

# logo_col, title_col = st.columns([1, 4])
# with title_col:
#     st.markdown("<h2 style='color:white; margin:0; line-height:1.2; text-align: center; margin-left:-220px;'>Tender Summarizer Studio</h2>", unsafe_allow_html=True)
#     st.markdown("<p style='color: #94a3b8; margin:0; font-size:14px; text-align: center;margin-left: -220px;'>Proprietary AI for procurement & bid engineering.</p>", unsafe_allow_html=True)

# st.write("##")

# # 4. CONTROL BAR (INPUTS)
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
#     analyze_button = st.button("Analyze Tender", use_container_width=True)
# st.markdown('</div>', unsafe_allow_html=True)

# # 5. BUTTON LOGIC (TRIGGER API)
# if analyze_button:
#     if uploaded_file:
#         with st.spinner("⏳ Analyzing tender document... (This may take 30-60s)"):
#             try:
#                 files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
#                 data = {
#                     "query": "Provide a comprehensive summary of this tender document including Scope, Requirements, and Deadlines.",
#                     "output_format": out_format,
#                     "depth": depth
#                 }
                
#                 # Call Backend
#                 response = requests.post("http://127.0.0.1:8000/analyze-tender", files=files, data=data, timeout=120)
                
#                 if response.status_code == 200:
#                     result = response.json()
#                     st.session_state.summary_result = result.get("summary", "No summary returned.")
                    
#                     # Generate PDF bytes and store in session state
#                     pdf = FPDF()
#                     pdf.add_page()
#                     pdf.set_font("Arial", size=12)
#                     clean_text = st.session_state.summary_result.encode('latin-1', 'replace').decode('latin-1')
#                     pdf.multi_cell(0, 10, txt=clean_text)
#                     st.session_state.pdf_bytes = bytes(pdf.output(dest='S'))
                    
#                     st.session_state.show_summary = True
#                     st.session_state.copy_status = "📋 Copy Summary"
#                     st.session_state.copy_success = False
#                     st.success("✅ Analysis complete!")
#                 else:
#                     st.error(f"Error {response.status_code}: {response.text}")
#             except Exception as e:
#                 st.error(f"Connection Error: {e}")
#                 st.info("Make sure 'rag_api.py' is running.")
#     else:
#         st.warning("⚠️ Please upload a PDF file first.")

# # 6. MAIN LAYOUT (DUAL PANE)
# col_left, col_right = st.columns(2, gap="medium")

# # --- LEFT PANE (PREVIEW) ---
# with col_left:
#     if uploaded_file:
#         base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
#         pdf_html = f"""
#         <div class="pane-container">
#             <div class="pane-header">Source Document Preview</div>
#             <iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="100%" style="border:none;"></iframe>
#         </div>
#         """
#         st.markdown(pdf_html, unsafe_allow_html=True)
#     else:
#         st.markdown("""
#         <div class="pane-container">
#             <div class="pane-header">Source Document Preview</div>
#             <div style="flex-grow:1; display:flex; align-items:center; justify-content:center; color:#484F58;">
#                 Awaiting Document Upload...
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

# # --- RIGHT PANE (RESULTS) ---
# with col_right:
#     if st.session_state.summary_result and st.session_state.show_summary:
#         # Prepare HTML for summary content
#         summary_html_content = st.session_state.summary_result.replace("\n", "<br>")
        
#         # Create the pane HTML
#         right_pane_html = f"""
#         <div class="pane-container">
#             <div class="pane-header">AI Generated Intelligence</div>
#             <div class="content-scroll">
#                 <div class="summary-content">
#                     <div class="summary-title">📊 Analysis Result</div>
#                     <div class="summary-text">{summary_html_content}</div>
#                     <hr class="divider">
#                 </div>
#             </div>
#         </div>
#         """
        
#         # Render the pane
#         st.markdown(right_pane_html, unsafe_allow_html=True)
#     else:
#         # Empty state
#         right_pane_html = """
#         <div class="pane-container">
#             <div class="pane-header">AI Generated Intelligence</div>
#             <div class="content-scroll">
#                 <div style="height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; color:#484F58; text-align:center;">
#                     <p style="font-size: 30px; margin-bottom: 10px;">📝</p>
#                     <p>Analysis results will appear here</p>
#                     <p style="font-size: 12px; margin-top: 10px; color: #8B949E;">Upload a PDF and click "Analyze Tender"</p>
#                 </div>
#             </div>
#         </div>
#         """
        
#         # Render empty pane
#         st.markdown(right_pane_html, unsafe_allow_html=True)

# # 7. ACTION BUTTONS ROW (Aligned under both panes)
# st.markdown('<div class="button-row">', unsafe_allow_html=True)

# # Create 3 equal columns for the buttons
# left_btn_col, middle_btn_col, right_btn_col = st.columns(3)

# with left_btn_col:
#     # Clear Results button
#     if st.session_state.show_summary:
#         if st.button("🗑️ Clear Results", 
#                     type="secondary", 
#                     use_container_width=True,
#                     key="clear_results"):
#             st.session_state.summary_result = None
#             st.session_state.pdf_bytes = None
#             st.session_state.show_summary = False
#             st.session_state.copy_status = "📋 Copy Summary"
#             st.session_state.copy_success = False
#             st.rerun()

# with middle_btn_col:
#     # Download PDF button
#     if st.session_state.show_summary and st.session_state.pdf_bytes and uploaded_file:
#         st.download_button(
#             label="📄 Download Report PDF",
#             data=st.session_state.pdf_bytes,
#             file_name=f"summary_{uploaded_file.name}.pdf",
#             mime="application/pdf",
#             use_container_width=True,
#             key="download_pdf"
#         )

# with right_btn_col:
#     # Copy Summary button with working copy functionality
#     if st.session_state.show_summary and st.session_state.summary_result:
#         # Create a hidden text area with the summary
#         summary_for_copy = st.session_state.summary_result
        
#         # Button to trigger copy
#         if st.button(st.session_state.copy_status, 
#                     use_container_width=True,
#                     key="copy_summary_btn",
#                     type="primary"):
            
#             # Use JavaScript to copy to clipboard
#             copy_js = f"""
#             <script>
#             // Create a temporary textarea
#             const textArea = document.createElement('textarea');
#             textArea.value = `{summary_for_copy.replace('`', '\\`').replace('\\\\', '\\\\\\\\')}`;
#             document.body.appendChild(textArea);
#             textArea.select();
#             document.execCommand('copy');
#             document.body.removeChild(textArea);
            
#             // Show success message
#             const event = new Event('copySuccess');
#             document.dispatchEvent(event);
#             </script>
#             """
#             st.markdown(copy_js, unsafe_allow_html=True)
            
#             # Update button status
#             st.session_state.copy_status = "✓ Copied!"
#             st.session_state.copy_success = True
            
#             # Force a rerun to update the UI
#             st.rerun()

# st.markdown('</div>', unsafe_allow_html=True)

# # Show success message when copied
# if st.session_state.copy_success:
#     success_html = """
#     <div style="background-color: #238636; color: white; padding: 10px 15px; border-radius: 8px; 
#                 margin-top: 10px; text-align: center; font-weight: 600; animation: fadeOut 2s ease-in-out;"
#          class="fade-out">
#         ✓ Summary copied to clipboard!
#     </div>
#     """
#     st.markdown(success_html, unsafe_allow_html=True)
    
#     # Reset after showing message
#     time.sleep(2)
#     st.session_state.copy_success = False
#     st.session_state.copy_status = "📋 Copy Summary"
#     st.rerun()


import streamlit as st
import time
import base64
import os
import requests
from pathlib import Path
import sys
import markdown2
from io import BytesIO
from xhtml2pdf import pisa


# FIX: Add the correct path to find components
current_dir = os.path.dirname(os.path.abspath(__file__))  # frontend/pages
parent_dir = os.path.dirname(current_dir)  # frontend/
sys.path.insert(0, parent_dir)

# Now import from components
try:
    from components.navbar import render_navbar
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.error(f"Current sys.path: {sys.path}")
    # Define a dummy render_navbar function as fallback
    def render_navbar():
        st.markdown("<div style='margin-bottom:20px;'>Navigation placeholder</div>", unsafe_allow_html=True)

# 1. PAGE CONFIG & SESSION STATE
st.set_page_config(page_title="TenderFlow AI | Analyzer", layout="wide")

if "summary_result" not in st.session_state:
    st.session_state.summary_result = None
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None
if "show_summary" not in st.session_state:
    st.session_state.show_summary = False
if "copy_status" not in st.session_state:
    st.session_state.copy_status = "📋 Copy Summary"
if "copy_success" not in st.session_state:
    st.session_state.copy_success = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False
if "edited_summary" not in st.session_state:
    st.session_state.edited_summary = None

# Professional PDF generation function (same as tenderGeneration)
def create_analysis_pdf(markdown_content: str) -> bytes:
    """
    Creates a professional PDF from markdown content using xhtml2pdf.
    """
    html_body = markdown2.markdown(
        markdown_content,
        extras=["tables", "fenced-code-blocks", "header-ids", "break-on-newline"]
    )
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: 'Times New Roman', Times, serif;
                font-size: 11pt;
                line-height: 1.6;
                color: #1a1a1a;
            }}
            h1 {{ font-size: 18pt; color: #1e3a5f; border-bottom: 2px solid #1e3a5f; padding-bottom: 5px; margin-top: 20px; }}
            h2 {{ font-size: 14pt; color: #2c5282; margin-top: 15px; }}
            h3 {{ font-size: 12pt; color: #2d3748; margin-top: 12px; }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                font-size: 10pt;
            }}
            th {{
                background-color: #2c3e50;
                color: white;
                padding: 10px;
                text-align: left;
                border: 1px solid #1a252f;
            }}
            td {{
                padding: 8px;
                border: 1px solid #ddd;
                vertical-align: top;
            }}
            tr:nth-child(even) {{ background-color: #f8f9fa; }}
            strong {{ color: #1e3a5f; }}
            ul, ol {{ margin-left: 20px; }}
            li {{ margin-bottom: 5px; }}
            .header {{
                text-align: center;
                border-bottom: 3px solid #1e3a5f;
                padding-bottom: 15px;
                margin-bottom: 20px;
            }}
            .footer {{
                text-align: center;
                font-size: 9pt;
                color: #666;
                margin-top: 30px;
                border-top: 1px solid #ddd;
                padding-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Tender Analysis Report</h1>
            <p style="color: #666; font-size: 10pt;">Generated by TenderFlow AI</p>
        </div>
        {html_body}
        <div class="footer">
            <p>This document was automatically generated. Please verify all information.</p>
        </div>
    </body>
    </html>
    """
    
    pdf_buffer = BytesIO()
    pisa.CreatePDF(html_template, dest=pdf_buffer)
    return pdf_buffer.getvalue()

# 2. CSS STYLING
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

/* Clean up Streamlit UI */
button[title="View header anchor"] { display: none !important; }
.stHtmlHeader a , .stMarkdown a{ display: none !important; }
header { visibility: hidden; }
      
.stApp {
    background-color: #0d1117;
    font-family: 'Inter', sans-serif;
}

/* Control Bar Styling */
.control-bar {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 25px;
    margin-top: -40px;
}

/* Button Styling */
div.stButton > button {
    background-color: #7c3aed !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    border: 1.5px solid #8b5cf6 !important;
    transition: 0.3s;
}

/* Clear Results Button Styling */
.clear-btn {
    background-color: #30363D !important;
    color: #c9d1d9 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    border: 1px solid #484F58 !important;
    transition: 0.3s !important;
}

.clear-btn:hover {
    background-color: #484F58 !important;
    border-color: #8B949E !important;
}

/* Pane Containers */
.pane-container {
    background-color: #0D1117;
    border: 1px solid #30363D;
    border-radius: 10px;
    height: 600px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: flex-start; /* FIX: Ensure content starts at top */
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

.label-tag { 
    color: #8B949E; 
    font-size: 12px; 
    font-weight: 700; 
    margin-bottom: 8px; 
    text-transform: uppercase; 
}

/* Result Scroll Area */
.content-scroll {
    padding: 20px; 
    color: #e6edf3; 
    height: 540px; 
    overflow-y: auto;
    font-size: 15px;
    line-height: 1.6;
}

/* Style for summary content */
.summary-content {
    margin-bottom: 20px;
}

.summary-title {
    color: #e6edf3;
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.summary-text {
    color: #c9d1d9;
    line-height: 1.6;
    margin-bottom: 20px;
    white-space: pre-wrap;
}

.divider {
    border: 0;
    height: 1px;
    background: #30363D;
    margin: 20px 0;
}

/* Button alignment container */
.button-row {
    display: flex;
    gap: 15px;
    margin-top: 20px;
    width: 100%;
}

.button-row > div {
    flex: 1;
}

/* Copy button styling */
.copy-success {
    background-color: #238636 !important;
    color: white !important;
    border-color: #2ea043 !important;
}
</style>
""", unsafe_allow_html=True)

# 3. NAVBAR & TITLE
render_navbar()

logo_col, title_col = st.columns([1, 4])
with title_col:
    st.markdown("<h2 style='color:white; margin:0; line-height:1.2; text-align: center; margin-left:-220px;'>Tender Summarizer Studio</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; margin:0; font-size:14px; text-align: center;margin-left: -220px;'>Proprietary AI for procurement & bid engineering.</p>", unsafe_allow_html=True)

st.write("##")

# 4. CONTROL BAR (INPUTS)
st.markdown('<div class="control-bar">', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])

with c1:
    st.markdown('<p class="label-tag">1. Document Upload</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload RFP", type=["pdf"], label_visibility="collapsed")

with c2:
    st.markdown('<p class="label-tag">2. Parsing Mode</p>', unsafe_allow_html=True)
    parsing_mode = st.selectbox("Parsing", ["Fast", "High-Quality"], label_visibility="collapsed", help="Fast: PyMuPDF (15-21x faster) | High-Quality: OCR for scanned pages")

with c3:
    st.markdown('<p class="label-tag">3. Output Format</p>', unsafe_allow_html=True)
    out_format = st.selectbox("Format", ["Executive Bullets", "Technical Narrative", "Compliance Matrix"], label_visibility="collapsed")

with c4:
    st.markdown('<p class="label-tag">4. Analysis Depth</p>', unsafe_allow_html=True)
    depth = st.selectbox("Depth", ["Standard", "Deep Dive"], label_visibility="collapsed")

with c5:
    st.markdown('<p class="label-tag">5. Execution</p>', unsafe_allow_html=True)
    analyze_button = st.button("⚡ Analyze", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# 5. BUTTON LOGIC (TRIGGER API)
if analyze_button:
    if uploaded_file:
        spinner_msg = "⚡ Fast analysis in progress..." if parsing_mode == "Fast" else "🔍 High-quality analysis (OCR enabled)..."
        with st.spinner(spinner_msg):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                data = {
                    "query": "Provide a comprehensive summary of this tender document including Scope, Requirements, and Deadlines.",
                    "output_format": out_format,
                    "depth": depth,
                    "parsing_mode": parsing_mode  # NEW: Pass parsing mode

                }
                
                # Call Backend
                # Increased timeout to 600s (10 min) for large High-Quality jobs
                response = requests.post("http://127.0.0.1:8000/analyze-tender", files=files, data=data, timeout=600)
                
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.summary_result = result.get("summary", "No summary returned.")
                    
                    # Generate PROFESSIONAL PDF using xhtml2pdf (same as tenderGeneration)
                    st.session_state.pdf_bytes = create_analysis_pdf(st.session_state.summary_result)
                    
                    st.session_state.show_summary = True
                    st.session_state.copy_status = "📋 Copy Summary"
                    st.session_state.copy_success = False
                    st.session_state.edit_mode = False
                    st.session_state.edited_summary = None
                    
                    # Show processing time if available
                    proc_time = result.get("processing_time", "")
                    cached = result.get("cached", False)
                    if cached:
                        st.success(f"✅ Analysis complete! (Cached index, {proc_time})")
                    else:
                        st.success(f"✅ Analysis complete! ({proc_time})")
                else:
                    st.error(f"Error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")
                st.info("Make sure 'rag_api.py' is running.")
    else:
        st.warning("⚠️ Please upload a PDF file first.")

# 6. MAIN LAYOUT (DUAL PANE)
col_left, col_right = st.columns(2, gap="medium")

# --- LEFT PANE (PREVIEW) ---
with col_left:
    if uploaded_file:
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        
        # For files > 5MB, render first page as image (FAST preview)
        if file_size_mb > 5:
            try:
                import fitz  # PyMuPDF
                
                # Load PDF and render first page as image
                pdf_bytes = uploaded_file.getvalue()
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                first_page = doc[0]
                
                # Render at 150 DPI for good quality but fast loading
                zoom = 150 / 72  # 150 DPI
                mat = fitz.Matrix(zoom, zoom)
                pix = first_page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                
                total_pages = len(doc)
                doc.close()
                
                st.markdown(f"""
                <div class="pane-container">
                    <div class="pane-header">Source Document Preview ({total_pages} pages, {file_size_mb:.1f} MB)</div>
                    <div style="flex-grow:1; overflow-y: auto; padding: 10px; background: #1a1a1a;">
                        <img src="data:image/png;base64,{img_base64}" style="width: 100%; border-radius: 4px; box-shadow: 0 2px 10px rgba(0,0,0,0.3);">
                        <p style="text-align: center; color: #6e7681; font-size: 11px; margin-top: 10px;">
                            Showing page 1 of {total_pages} (fast preview mode)
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                # Fallback to file info if fitz fails
                st.markdown(f"""
                <div class="pane-container">
                    <div class="pane-header">Source Document Preview</div>
                    <div style="flex-grow:1; display:flex; flex-direction:column; align-items:center; justify-content:center; color:#8B949E;">
                        <p style="font-size: 40px;">📄</p>
                        <p>{uploaded_file.name}</p>
                        <p>Size: {file_size_mb:.1f} MB</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Normal preview for smaller files
            base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
            pdf_html = f"""
            <div class="pane-container">
                <div class="pane-header">Source Document Preview ({file_size_mb:.1f} MB)</div>
                <iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="100%" style="border:none;"></iframe>
            </div>
            """
            st.markdown(pdf_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="pane-container">
            <div class="pane-header">Source Document Preview</div>
            <div style="flex-grow:1; display:flex; align-items:center; justify-content:center; color:#484F58;">
                Awaiting Document Upload...
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- RIGHT PANE (RESULTS) ---
with col_right:
    if st.session_state.summary_result and st.session_state.show_summary:
        # Edit toggle and header
        st.markdown('<div class="pane-header" style="display: flex; justify-content: space-between; align-items: center;">AI Generated Intelligence <span id="edit-toggle"></span></div>', unsafe_allow_html=True)
        
        # Edit toggle checkbox
        col_title, col_edit = st.columns([0.8, 0.2])
        with col_edit:
            edit_mode = st.checkbox("✏️ Edit", key="edit_toggle", value=st.session_state.edit_mode)
            st.session_state.edit_mode = edit_mode
        
        # Get current content (edited or original)
        current_content = st.session_state.edited_summary if st.session_state.edited_summary else st.session_state.summary_result
        
        if edit_mode:
            # TEXT EDITOR MODE
            edited_content = st.text_area(
                "Edit Summary",
                value=current_content,
                height=500,
                label_visibility="collapsed",
                key="summary_editor"
            )
            st.session_state.edited_summary = edited_content
            
            # Save changes button
            if st.button("💾 Save & Update PDF", use_container_width=True):
                st.session_state.summary_result = edited_content
                st.session_state.pdf_bytes = create_analysis_pdf(edited_content)
                st.session_state.edit_mode = False
                st.success("Changes saved!")
                st.rerun()
        else:
            # PREVIEW MODE - Rich rendered markdown
            # Use markdown2 to generate HTML so we can embed it inside the scrolling div
            # This fixes the alignment issue where content was pushed down/outside
            html_content = markdown2.markdown(
                current_content,
                extras=["tables", "fenced-code-blocks", "header-ids"]
            )
            
            st.markdown(f"""
            <div class="pane-container">
                <div class="content-scroll" style="
                    background-color: white;
                    padding: 20px;
                    border-radius: 8px;
                    color: #1a1a1a;
                    /* font-family preserved as default (sans-serif) as user liked it */
                    font-size: 11pt;
                    line-height: 1.6;
                    height: 100%;
                    overflow-y: auto;
                ">
                    {html_content}
                </div>
            </div>
            """, unsafe_allow_html=True)

    else:
        # Empty state
        right_pane_html = """
        <div class="pane-container">
            <div class="pane-header">AI Generated Intelligence</div>
            <div class="content-scroll">
                <div style="height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; color:#484F58; text-align:center;">
                    <p style="font-size: 30px; margin-bottom: 10px;">📝</p>
                    <p>Analysis results will appear here</p>
                    <p style="font-size: 12px; margin-top: 10px; color: #8B949E;">Upload a PDF and click "⚡ Analyze"</p>
                </div>
            </div>
        </div>
        """


        
        # Render empty pane
        st.markdown(right_pane_html, unsafe_allow_html=True)

# 7. ACTION BUTTONS ROW
st.markdown('<div class="button-row">', unsafe_allow_html=True)
left_btn_col, middle_btn_col, right_btn_col = st.columns(3)

with left_btn_col:
    if st.session_state.show_summary:
        if st.button("🗑️ Clear Results", use_container_width=True, key="clear_results"):
            st.session_state.summary_result = None
            st.session_state.show_summary = False
            st.session_state.copy_status = "📋 Copy Summary"
            st.session_state.copy_success = False
            st.rerun()

with middle_btn_col:
    if st.session_state.show_summary and st.session_state.pdf_bytes and uploaded_file:
        st.download_button(
            label="📄 Download Report PDF",
            data=st.session_state.pdf_bytes,
            file_name=f"summary_{uploaded_file.name}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="download_pdf"
        )

with right_btn_col:
    if st.session_state.show_summary and st.session_state.summary_result:
        # Get current content for copy
        current = st.session_state.edited_summary if st.session_state.edited_summary else st.session_state.summary_result
        
        # Use pyperclip-style copy with download button workaround
        st.download_button(
            label=st.session_state.copy_status,
            data=current,
            file_name="summary.txt",
            mime="text/plain",
            use_container_width=True,
            key="copy_as_txt",
            help="Click to download summary as text file"
        )

st.markdown('</div>', unsafe_allow_html=True)

# 8. FOOTER SUCCESS MESSAGE  
if st.session_state.copy_success:
    st.toast("Summary copied to clipboard!", icon="✅")
    st.session_state.copy_success = False
    st.session_state.copy_status = "📋 Copy Summary"
