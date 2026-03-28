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
from utils.auth import can_access

# API Configuration: Use Render URL by default, fallback to localhost for dev
API_BASE_URL = os.environ.get(
    "API_BASE_URL",
    "https://tenderflow-iwpl.onrender.com"
)
# Override to localhost if explicitly running in dev mode
if os.environ.get("TENDERFLOW_ENV", "").lower() == "dev":
    API_BASE_URL = "http://127.0.0.1:8000"


# Now import from components
# try:
#     from components.navbar import render_navbar
# except ImportError as e:
#     st.error(f"Import Error: {e}")
#     st.error(f"Current sys.path: {sys.path}")
#     # Define a dummy render_navbar function as fallback
#     def render_navbar():
#         st.markdown("<div style='margin-bottom:20px;'>Navigation placeholder</div>", unsafe_allow_html=True)
def get_base64_of_bin_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

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
                margin: 20mm 15mm 20mm 15mm;
            }}
            body {{
                font-family: 'Helvetica', 'Arial', sans-serif;
                font-size: 11pt;
                line-height: 1.6;
                color: #333333;
                text-align: justify;
            }}
            h1 {{
                font-size: 22pt;
                color: #1e3a8a;
                text-transform: uppercase;
                text-align: center;
                border-bottom: 3px solid #1e3a8a;
                padding-bottom: 10px;
                margin-bottom: 25px;
            }}
            h2 {{
                font-size: 15pt;
                color: #2563eb;
                margin-top: 30px;
                margin-bottom: 15px;
                border-bottom: 1px solid #d1d5db;
                padding-bottom: 5px;
            }}
            h3 {{
                font-size: 13pt;
                color: #1f2937;
                margin-top: 20px;
                margin-bottom: 10px;
                font-weight: bold;
            }}
            p {{ margin-bottom: 12px; }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th {{
                background-color: #1e3a8a;
                color: #ffffff;
                font-weight: bold;
                padding: 12px;
                text-align: left;
                border: 1px solid #1e3a8a;
            }}
            td {{
                padding: 10px 12px;
                border: 1px solid #e5e7eb;
                vertical-align: top;
            }}
            tr:nth-child(even) {{ background-color: #f3f4f6; }}
            ul, ol {{ margin-left: 20px; margin-bottom: 15px; }}
            li {{ margin-bottom: 8px; }}
            blockquote {{
                border-left: 4px solid #3b82f6;
                background-color: #eff6ff;
                padding: 15px;
                margin: 20px 0;
                color: #1e40af;
                font-style: italic;
            }}
            .header {{
                text-align: center;
                margin-bottom: 40px;
                padding: 30px 20px;
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }}
            .header-logo {{
                font-size: 26pt;
                font-weight: bold;
                color: #0f172a;
                letter-spacing: 1px;
                border-bottom: 1px solid #cbd5e1;
                padding-bottom: 10px;
                margin-bottom: 10px;
            }}
            .header-sub {{
                font-size: 11pt;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 2px;
                font-weight: bold;
            }}
            .footer {{
                text-align: center;
                font-size: 9pt;
                color: #94a3b8;
                margin-top: 50px;
                border-top: 1px solid #e2e8f0;
                padding-top: 15px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-logo">Tender Document Analysis</div>
            <div class="header-sub">Proprietary Analytical Report • TenderFlow AI</div>
        </div>
        {html_body}
        <div class="footer">
            Generated securely by Tender Summarizer Studio | Confidential Report
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
            background: radial-gradient(circle at 20% 30%, #1a1c4b 0%, #0f111a 100%) !important;
        }
        [data-testid="stAppViewContainer"] {
            background: transparent !important;
        }
        [data-testid="stHeader"] {
            background: rgba(2, 6, 23, 0.85) !important;
        }

div.block-container {
    padding-top: 0.3rem !important; 
}

/* HEADER NAV CONTAINER */
.header-nav {
    background: linear-gradient(
        135deg,
        rgba(255,255,255,0.08),
        rgba(255,255,255,0.02)
    );
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px;
    padding: 12px 18px;
    margin-bottom: 22px;
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

# # 3. NAVBAR & TITLE
# render_navbar()

# HEADER NAVIGATION
left, center = st.columns([3, 6])

with left:
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
    logo = get_base64_of_bin_file(logo_path)

    if logo:
        st.markdown(f"""
            <div style="display:flex; align-items:center;">
                <img src="data:image/png;base64,{logo}" width="180">
            </div>
        """, unsafe_allow_html=True)

with center:
    header_cols = st.columns([3, 0.4, 0.4, 0.4, 0.4, 0.4])

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
        else:
            st.button("⬈", key="h_risk_disabled", disabled=True)

logo_col, title_col = st.columns([1, 4])
with title_col:
    st.markdown("<h2 style='color:white; margin:0; line-height:1.2; text-align: center; margin-left:-220px;margin-top:20px;font-size:50px'>Tender Summarizer Studio</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; margin:0; font-size:14px; text-align: center;margin-left: -220px;'>Proprietary AI for procurement & bid engineering.</p>", unsafe_allow_html=True)

st.write("##")

# 4. CONTROL BAR (INPUTS)
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
        spinner_msg = "⚡ Generating detailed report (this may take 30-60s)..." if parsing_mode == "Fast" else "🔍 High-quality analysis & OCR (this may take 2-3 mins)..."
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
                response = requests.post(f"{API_BASE_URL}/analyze-tender", files=files, data=data, timeout=600)
                
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.summary_result = result.get("summary", "No summary returned.")
                    
                    # Generate PROFESSIONAL PDF using xhtml2pdf (same as tenderGeneration)
                    with st.spinner("📄 Generating PDF Report..."):
                        try:
                            st.session_state.pdf_bytes = create_analysis_pdf(st.session_state.summary_result)
                        except TypeError as pdf_err:
                            # Guard against xhtml2pdf 'NotImplementedType' CSS parsing errors
                            st.warning(f"PDF generation encountered a non-critical issue: {pdf_err}. You can still view the summary below.")
                            st.session_state.pdf_bytes = None
                    
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
                import traceback
                traceback.print_exc()
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
            # PREVIEW MODE - Rich rendered markdown
            # Removed fenced-code-blocks to avoid showing code snippets styled boxes
            html_content = markdown2.markdown(
                current_content,
                extras=["tables", "header-ids"]
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
left_btn_col, middle_btn_col = st.columns(2)

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

st.markdown('</div>', unsafe_allow_html=True)

# 8. FOOTER SUCCESS MESSAGE  
if st.session_state.copy_success:
    st.toast("Summary copied to clipboard!", icon="✅")
    st.session_state.copy_success = False
    st.session_state.copy_status = "📋 Copy Summary"
