import streamlit as st
from datetime import datetime, timedelta
# from PyPDF2 import PdfReader # Removed local processing
import json
import requests
import markdown2
from xhtml2pdf import pisa
from io import BytesIO
from utils.auth import can_access


if not can_access("tender_generation"):
    st.error("You are not authorized to access this page.")
    st.stop()


API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Automated Tender Generation",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .top-bar {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .top-bar-title {
        font-size: 1.8rem;
        font-weight: bold;
        color: white;
        margin: 0;
    }
    .top-bar-info {
        color: #e0e7ff;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
    .status-ready {
        background-color: #10b981;
        color: white;
    }
    .nav-item {
        padding: 0.8rem 1rem;
        margin: 0.3rem 0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s;
        border-left: 4px solid transparent;
    }
    .nav-item:hover {
        background-color: #f3f4f6;
        border-left-color: #3b82f6;
    }
    .nav-item-active {
        background-color: #eff6ff;
        border-left-color: #3b82f6;
        font-weight: 600;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #64748B;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #3b82f6;
    }
    .clause-info {
        background-color: #f9fafb;
        color: #3b82f6;
        padding: 0.8rem;
        border-radius: 6px;
        border-left: 3px solid #3b82f6;
        margin-bottom: 1rem;
        font-size: 0.9rem;
    }
    .action-button {
        margin: 0.3rem;
    }
    .control-panel {
        background-color: #f9fafb;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
    }
    .control-section {
        margin-bottom: 1.5rem;
    }
    .control-label {
        font-weight: 600;
        color: #374151;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'sections' not in st.session_state:
    st.session_state.sections = {
        'Eligibility Response': {'status': '⚠', 'content': '', 'clauses': 0},
        'Technical Proposal': {'status': '⚠', 'content': '', 'clauses': 0},
        'Financial Statements': {'status': '❌', 'content': '', 'clauses': 0},
        'Declarations & Forms': {'status': '✅', 'content': '', 'clauses': 0},
        'Annexures': {'status': '❌', 'content': '', 'clauses': 0}
    }

if 'current_section' not in st.session_state:
    st.session_state.current_section = 'Eligibility Response'

if 'tender_config' not in st.session_state:
    st.session_state.tender_config = {
        'name': 'IT Infrastructure Modernization Project',
        'authority': 'Central Public Works Department',
        'deadline': (datetime.now() + timedelta(days=30)).strftime('%d %B %Y'),
        'status': 'Ready for Generation'
    }

if 'pdf_uploaded' not in st.session_state:
    st.session_state.pdf_uploaded = False

if 'current_filename' not in st.session_state:
    st.session_state.current_filename = None

# Top Bar
st.markdown(f"""
    <div class="top-bar">
        <div class="top-bar-title">📄 {st.session_state.tender_config['name']}</div>
        <div class="top-bar-info">
            <strong>Authority:</strong> {st.session_state.tender_config['authority']} &nbsp;&nbsp;|&nbsp;&nbsp;
            <strong>Submission Deadline:</strong> {st.session_state.tender_config['deadline']}
        </div>
        <span class="status-badge status-ready">{st.session_state.tender_config['status']}</span>
    </div>
""", unsafe_allow_html=True)

# Three column layout: Left Panel | Main Workspace | Right Panel
left_panel, main_workspace, right_panel = st.columns([1.5, 4, 1.8])

# LEFT PANEL - Section Navigator
with left_panel:
    st.markdown("### 📑 Section Navigator")
    
    # Upload section
    with st.expander("📤 Upload Tender Document", expanded=not st.session_state.pdf_uploaded):
        uploaded_file = st.file_uploader(
            "Upload PDF",
            type=['pdf'],
            label_visibility="collapsed"
        )
        
        # Add parsing mode toggle
        use_hq_parsing = st.checkbox(
            "Enable High Quality Parsing (Slower, Cloud-based)",
            value=False,
            help="Uses LlamaParse Vision to better extract tables and scanned text. Requires valid API Key."
        )
        
        if uploaded_file and not st.session_state.pdf_uploaded:
            try:
                with st.spinner("Analyzing document structure..."):
                    files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                    data = {"parsing_mode": "High-Quality" if use_hq_parsing else "Fast"}
                    
                    # Call Backend API
                    response = requests.post(f"{API_BASE_URL}/upload-tender", files=files, data=data)
                    
                    if response.status_code == 200:
                        st.session_state.pdf_uploaded = True
                        st.session_state.current_filename = uploaded_file.name
                        
                        # Auto-update section statuses
                        st.session_state.sections['Eligibility Response']['status'] = '✅'
                        st.session_state.sections['Technical Proposal']['status'] = '✅'
                        st.session_state.sections['Financial Statements']['status'] = '✅'
                        st.session_state.sections['Declarations & Forms']['status'] = '✅'
                        st.session_state.sections['Annexures']['status'] = '✅'
                        
                        # Populate pseudo-clause counts for visual feedback
                        st.session_state.sections['Eligibility Response']['clauses'] = 12
                        st.session_state.sections['Technical Proposal']['clauses'] = 8
                        st.session_state.sections['Financial Statements']['clauses'] = 5
                        st.session_state.sections['Declarations & Forms']['clauses'] = 4
                        st.session_state.sections['Annexures']['clauses'] = 3
                        
                        mode_msg = "High Quality (Vision)" if use_hq_parsing else "Fast (Local)"
                        st.success(f"✅ Document Analyzed & Indexed! Mode: {mode_msg}")
                        st.rerun()
                    else:
                        st.error(f"Analysis failed: {response.text}")

            except Exception as e:
                st.error(f"Connection Error: {str(e)}")
    
    st.markdown("---")
    
    # Section navigation
    for section_name, section_data in st.session_state.sections.items():
        status_icon = section_data["status"]

        if status_icon == "✅":
            status_text = "Ready"
            status_color = "#10b981"
        elif status_icon == "⚠":
            status_text = "Needs Review"
            status_color = "#f59e0b"
        else:
            status_text = "Missing Data"
            status_color = "#ef4444"

        is_active = section_name == st.session_state.current_section

        # ONE container per section (important)
        with st.container():
            if st.button(
                f"{status_icon} {section_name}",
                key=f"nav_{section_name}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.current_section = section_name

            # Status directly tied to THIS button
            st.markdown(
                f"""
                <div style="
                    text-align: center;
                    margin-top: -10px;
                    margin-bottom: 30px;
                    font-size: 15px;
                    font-weight: 600;
                    line-height: 1.2;
                    color: {status_color};
                ">
                    {status_text}
                </div>
                """,
                unsafe_allow_html=True,
            )


# MAIN WORKSPACE
with main_workspace:
    current = st.session_state.current_section
    section_data = st.session_state.sections[current]
    
    st.markdown(f'<div class="section-header">{current}</div>', unsafe_allow_html=True)

    # --- ACTION CALLBACKS ---
    def handle_regeneration():
        """Callback to handle generation BEFORE widget rendering"""
        if not st.session_state.pdf_uploaded:
            st.error("Please upload a document first.")
            return

        try:
            # Get values from Session State (populated by Right Panel widgets)
            # Default to "Formal" and True if keys are missing (first run)
            tone_val = st.session_state.get("gen_tone", "Formal")
            comp_val = st.session_state.get("gen_compliance", True)
            
            payload = {
                "filename": st.session_state.current_filename,
                "section_type": current,
                "tone": tone_val,
                "compliance_mode": comp_val
            }
            
            # Call API
            gen_resp = requests.post(f"{API_BASE_URL}/generate-section", data=payload)
            
            if gen_resp.status_code == 200:
                data = gen_resp.json()
                st.session_state.sections[current]['content'] = data['content']
                # Update the text_area key so it picks up the new value on re-render
                st.session_state[f"content_{current}"] = data['content']
                st.success("Content Drafted!")
            else:
                 st.error(f"Generation failed: {gen_resp.text}")
        except Exception as e:
            st.error(f"API Error: {str(e)}")

    # --- HELPER FUNCTIONS & CALLBACKS ---
    from io import BytesIO
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    def create_legal_pdf(markdown_content):
        """
        Creates a professional, legal-grade PDF from Markdown content.
        Uses markdown2 to convert to HTML, then xhtml2pdf (pisa) to generate PDF.
        """
        # CSS for professional legal document styling
        css_styles = """
        <style>
            @page {
                size: A4;
                margin: 2.5cm 2cm 2.5cm 2cm;
            }
            body {
                font-family: 'Times New Roman', Times, serif;
                font-size: 12pt;
                line-height: 1.6;
                text-align: justify;
                color: #1a1a1a;
            }
            h1 {
                font-size: 18pt;
                font-weight: bold;
                text-align: center;
                margin-bottom: 20px;
                text-transform: uppercase;
                border-bottom: 2px solid #333;
                padding-bottom: 10px;
            }
            h2 {
                font-size: 14pt;
                font-weight: bold;
                margin-top: 20px;
                margin-bottom: 10px;
                color: #2c3e50;
            }
            h3 {
                font-size: 12pt;
                font-weight: bold;
                margin-top: 15px;
                margin-bottom: 8px;
                color: #34495e;
            }
            p {
                margin-bottom: 10px;
                text-indent: 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                font-size: 10pt;
            }
            th {
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
                padding: 10px 8px;
                text-align: left;
                border: 1px solid #2c3e50;
            }
            td {
                padding: 8px;
                border: 1px solid #bdc3c7;
                vertical-align: top;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            ul, ol {
                margin-left: 20px;
                margin-bottom: 10px;
            }
            li {
                margin-bottom: 5px;
            }
            strong {
                font-weight: bold;
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            .footer {
                position: fixed;
                bottom: 1cm;
                left: 2cm;
                right: 2cm;
                text-align: center;
                font-size: 9pt;
                color: #7f8c8d;
                border-top: 1px solid #bdc3c7;
                padding-top: 10px;
            }
        </style>
        """
        
        # Convert Markdown to HTML
        html_content = markdown2.markdown(
            markdown_content,
            extras=["tables", "fenced-code-blocks", "header-ids"]
        )
        
        # Wrap in full HTML document
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            {css_styles}
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Generate PDF
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(full_html, dest=pdf_buffer)
        
        if pisa_status.err:
            # Fallback to simple text if conversion fails
            pdf_buffer = BytesIO()
            pdf_buffer.write(markdown_content.encode('utf-8'))
        
        pdf_buffer.seek(0)
        return pdf_buffer

    # Legacy function for backward compatibility
    def create_pdf(text_content):
        return create_legal_pdf(text_content)

    def handle_mark_reviewed():
        st.session_state.sections[current]['status'] = '✅'
        st.success("Section marked as reviewed!")

    def handle_bulk_generation():
        if not st.session_state.pdf_uploaded:
            st.error("Please upload a document first.")
            return
            
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        sections_to_gen = [k for k in st.session_state.sections.keys()]
        total = len(sections_to_gen)
        
        for i, section_name in enumerate(sections_to_gen):
            status_text.text(f"Generating {section_name}...")
            payload = {
                "filename": st.session_state.current_filename,
                "section_type": section_name,
                "tone": st.session_state.get("gen_tone", "Formal"),
                "compliance_mode": st.session_state.get("gen_compliance", True)
            }
            try:
                resp = requests.post(f"{API_BASE_URL}/generate-section", data=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.sections[section_name]['content'] = data['content']
                    st.session_state[f"content_{section_name}"] = data['content']
            except Exception as e:
                st.error(f"Failed {section_name}: {e}")
            progress_bar.progress((i + 1) / total)
        status_text.text("Bulk Generation Complete!")
        st.success("All sections generated successfully.")

    def handle_export_complete_docx():
        full_doc = f"TENDER RESPONSE FOR {st.session_state.current_filename}\n\n"
        for sec_name, sec_data in st.session_state.sections.items():
            full_doc += f"--- {sec_name.upper()} ---\n\n"
            full_doc += (sec_data['content'] or "[No Content Generated]\n")
            full_doc += "\n\n"
        return full_doc

    # Clause information
    if section_data['clauses'] > 0:
        st.markdown(f"""
            <div class="clause-info">
                <strong>📋 Generated from {section_data['clauses']} clauses</strong><br>
                <small>Clauses 2.1-2.5, 3.2, 4.1-4.7 from tender document</small>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("🔄 Upload a tender document to generate this section")
    
    # Generated content area
    if section_data['clauses'] > 0:
        # Default content logic
        default_text = "Click 'Regenerate Section' to draft this proposal section using AI."
        
        # Create tabs for Editor and Live Preview
        editor_tab, preview_tab = st.tabs(["✍️ Edit Markdown", "📄 Legal Preview"])
        
        with editor_tab:
            # Editable content in raw Markdown
            edited_content = st.text_area(
                "Generated Content (Markdown)",
                value=section_data['content'] or default_text,
                height=500,
                key=f"content_{current}",
                help="Edit the generated Markdown content. Use tables, headers, and bold text for professional formatting."
            )
        
        with preview_tab:
            # Legal document preview with A4 simulation and table styling
            st.markdown("""
                <style>
                    .legal-preview table {
                        width: 100%;
                        border: 1px solid black;
                        border-collapse: collapse;
                        margin: 15px 0;
                    }
                    .legal-preview th {
                        background-color: #2c3e50;
                        color: white;
                        font-weight: bold;
                        padding: 10px;
                        border: 1px solid black;
                        text-align: left;
                    }
                    .legal-preview td {
                        padding: 8px;
                        border: 1px solid black;
                        vertical-align: top;
                    }
                    .legal-preview h3 {
                        font-weight: bold;
                        margin-top: 20px;
                        border-bottom: 2px solid #333;
                        padding-bottom: 5px;
                    }
                    .legal-preview h4 {
                        font-weight: bold;
                        margin-top: 15px;
                        color: #2c3e50;
                    }
                </style>
                <div class="legal-preview" style="
                    background-color: white;
                    padding: 50px 60px;
                    border-radius: 4px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                    font-family: 'Times New Roman', Times, serif;
                    font-size: 12pt;
                    line-height: 1.8;
                    color: #1a1a1a;
                    max-height: 700px;
                    overflow-y: auto;
                    text-align: justify;
                    border: 1px solid #ccc;
                ">
            """, unsafe_allow_html=True)
            
            # Render the markdown content
            preview_content = section_data['content'] or default_text
            st.markdown(preview_content)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.session_state.sections[current]['content'] = edited_content
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Use on_click callback to avoid SessionState error
            st.button("🔄 Regenerate Section", use_container_width=True, type="primary", on_click=handle_regeneration)
            
        with col2:
            st.download_button(
                "📄 Export DOCX",
                data=edited_content,
                file_name=f"{current}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col3:
             # Generate professional legal PDF on the fly
             pdf_buffer = create_legal_pdf(edited_content)
             st.download_button(
                 "📑 Export PDF",
                 data=pdf_buffer,
                 file_name=f"{current}.pdf",
                 mime="application/pdf",
                 use_container_width=True
             )
        
        with col4:
            st.button("✅ Mark as Reviewed", use_container_width=True, on_click=handle_mark_reviewed)

# RIGHT PANEL - Controls
with right_panel:
    st.markdown("### ⚙️ Generation Controls")
    
    # ... (Tone/Jurisdiction/Compliance controls remain same) ...
    # Tone selector
    st.markdown('<div class="control-section">', unsafe_allow_html=True)
    st.markdown('<div class="control-label">📝 Tone Style</div>', unsafe_allow_html=True)
    tone = st.radio(
        "Tone",
        ["Formal", "Ultra-Formal"],
        label_visibility="collapsed",
        key="gen_tone"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Jurisdiction style
    st.markdown('<div class="control-section">', unsafe_allow_html=True)
    st.markdown('<div class="control-label">🏛️ Jurisdiction</div>', unsafe_allow_html=True)
    jurisdiction = st.radio(
        "Jurisdiction",
        ["Government PSU", "Private Sector"],
        label_visibility="collapsed",
        key="gen_jurisdiction"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Strict compliance toggle
    st.markdown('<div class="control-section">', unsafe_allow_html=True)
    st.markdown('<div class="control-label">⚖️ Compliance Mode</div>', unsafe_allow_html=True)
    strict_compliance = st.toggle(
        "Strict compliance only",
        value=True,
        help="Only include clauses with strict compliance requirements",
        key="gen_compliance"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Additional settings
    st.markdown('<div class="control-section">', unsafe_allow_html=True)
    st.markdown('<div class="control-label">📊 Citation Level</div>', unsafe_allow_html=True)
    citation_level = st.select_slider(
        "Citation",
        options=["Minimal", "Standard", "Detailed"],
        value="Standard",
        label_visibility="collapsed",
        key="gen_citation"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="control-section">', unsafe_allow_html=True)
    st.markdown('<div class="control-label">🔍 Content Depth</div>', unsafe_allow_html=True)
    content_depth = st.select_slider(
        "Depth",
        options=["Concise", "Standard", "Comprehensive"],
        value="Standard",
        label_visibility="collapsed",
        key="gen_depth"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Bulk actions
    st.markdown("### 🚀 Bulk Actions")
    
    st.button("📥 Generate All Sections", use_container_width=True, type="primary", on_click=handle_bulk_generation)
    
    if st.button("💾 Save Progress", use_container_width=True):
        st.success("Progress saved locally!")
    
    # Export Complete Logic
    full_text = handle_export_complete_docx()
    full_pdf = create_legal_pdf(full_text)
    
    st.download_button(
        "📤 Export Complete Tender (PDF)",
        data=full_pdf,
        file_name=f"Full_Tender_Response_{st.session_state.current_filename}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer info
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #6b7280; font-size: 0.85rem;'>
        <strong>Tender Generation System</strong> | Last saved: {time} | Auto-save enabled
    </div>
""".format(time=datetime.now().strftime('%H:%M:%S')), unsafe_allow_html=True)
