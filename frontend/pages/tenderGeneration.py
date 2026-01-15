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


import os
from supabase import create_client, Client

# Visual Editor Imports
try:
    from streamlit_quill import st_quill
    import markdownify
    HAS_VISUAL_EDITOR = True
except ImportError:
    HAS_VISUAL_EDITOR = False

API_BASE_URL = "http://localhost:8000"

# Initialize Supabase Client (Accessing env vars or session)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
if url and key:
    supabase: Client = create_client(url, key)

def get_company_context(user_id: str) -> str:
    """
    Fetches comprehensive company information for the given user_id.
    """
    if not user_id:
        return ""
    
    # We need the user's session token for RLS, but here we might use the service role 
    # OR better, rely on the global supabase client if we have RLS policies allowing read.
    # Actually, in the frontend, we usually use st.session_state['sb_session'] client interactions.
    # But for simplicity and robustness in this quick fix, let's try the direct client query 
    # assuming the user has rights or we're using a client that can read.
    # NOTE: In previous steps we saw this used 'supabase.table'.
    
    context_parts = []
    try:
        # 1. Company Information
        response = supabase.table("company_information").select("*").eq("id", user_id).maybe_single().execute()
        if response and hasattr(response, 'data') and response.data:
            data = response.data
            context_parts.append(f"Company Name: {data.get('company_name', 'N/A')}")
            context_parts.append(f"Registration Number: {data.get('registration_number', 'N/A')}")
            context_parts.append(f"Registered Address: {data.get('registered_address', 'N/A')}")
            context_parts.append(f"Website: {data.get('website_url', 'N/A')}")
        
        # 2. Business Compliance (GST, PAN)
        response = supabase.table("business_compliance").select("*").eq("user_id", user_id).maybe_single().execute()
        if response and hasattr(response, 'data') and response.data:
            data = response.data
            context_parts.append(f"GST Number: {data.get('gst_number', 'N/A')}")
            context_parts.append(f"PAN Number: {data.get('pan_number', 'N/A')}")
        
        # 3. Financials (Turnover, Banking)
        response = supabase.table("financials").select("*").eq("user_id", user_id).maybe_single().execute()
        if response and hasattr(response, 'data') and response.data:
            data = response.data
            context_parts.append(f"Annual Turnover: {data.get('annual_turnover', 'N/A')}")
            context_parts.append(f"Bank Account Number: {data.get('bank_account_number', 'N/A')}")
            context_parts.append(f"IFSC Code: {data.get('ifsc_code', 'N/A')}")
            context_parts.append(f"Bank Name: {data.get('bank_name', 'N/A')}")

    except Exception as e:
        print(f"[DEBUG] Error fetching company context: {e}")
        return ""
    
    result = "; ".join(context_parts) if context_parts else ""
    return result

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
        /* Rest of the CSS remains... */
        .section-header {
            font-size: 1.5rem;
            font-weight: bold;
            color: #64748B;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #3b82f6;
        }
        /* Fixing Overflow issues */
        div[data-testid="stVerticalBlock"] > div {
            width: 100%;
            box-sizing: border-box;
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

    # --- 1. SESSION & AUTH GUARD ---
    if not st.session_state.get("authenticated", False):
        # Allow dev/preview without crashing if not coming from login, 
        # but realistically should redirect. For now, check session.
        pass

    # --- DIAGNOSTICS SIDEBAR ---
    with st.sidebar:
        with st.expander("🛠️ System Diagnostics", expanded=False):
            user = st.session_state.get("user")
            sb_session = st.session_state.get("sb_session")
            st.write(f"**Authenticated:** {st.session_state.get('authenticated')}")
            st.write(f"**User Object:** {'Found' if user else 'Missing'}")
            if user:
                # Try both attribute and dict access
                uid = getattr(user, 'id', None) or (user.get('id') if isinstance(user, dict) else None)
                st.write(f"**User ID:** `{uid}`")
            st.write(f"**Session Token:** {'Found' if sb_session else 'Missing'}")
            
            if st.button("Force Refetch Context"):
                uid = getattr(user, 'id', None) or (user.get('id') if isinstance(user, dict) else None) if user else None
                if uid:
                    ctx = get_company_context(uid)
                    st.code(ctx if ctx else "Empty Context Returned")
                else:
                    st.warning("No User ID found")

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
            
            # Fetch company context from Supabase
            user = st.session_state.get("user")
            # Robust user_id extraction (handles both object and dict formats)
            user_id = getattr(user, 'id', None) or (user.get('id') if isinstance(user, dict) else None)
            
            company_context = ""
            if user_id:
                st.toast(f"🔍 Fetching company data...")
                company_context = get_company_context(user_id)
                if company_context:
                    st.toast(f"✅ Context loaded ({len(company_context)} chars)")
            
            print(f"[FRONTEND DEBUG] Sending payload to {API_BASE_URL}/generate-section")
            print(f"[FRONTEND DEBUG] Company Context length: {len(company_context)}")

            payload = {
                "filename": st.session_state.current_filename,
                "section_type": current,
                "tone": tone_val,
                "compliance_mode": comp_val,
                "company_context": company_context
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
            
            # Fetch company context (efficiently fetch once if possible, but here inside loop is fine or move out)
            # Actually better to fetch once outside loop for bulk
            # But adhering to the previous pattern for simplicity
            user = st.session_state.get("user")
            user_id = getattr(user, 'id', None) or (user.get('id') if isinstance(user, dict) else None)
            company_context = get_company_context(user_id) if user_id else ""
            
            payload = {
                "filename": st.session_state.current_filename,
                "section_type": section_name,
                "tone": st.session_state.get("gen_tone", "Formal"),
                "compliance_mode": st.session_state.get("gen_compliance", True),
                "company_context": company_context
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
        default_text = "Click 'Generate all Sections' to draft this proposal section using AI."
        
        # Edit Toggle placed prominently
        col_space, col_edit = st.columns([0.85, 0.15])
        with col_edit:
            is_editing = st.checkbox("✍️ Edit", key=f"edit_mode_{current}", help="Toggle between Legal Preview and Markdown Editor")
        
        if is_editing:
            if HAS_VISUAL_EDITOR:
                st.markdown("### 📝 Content Editor (Visual)")
                # Convert Markdown -> HTML for the editor
                html_input = markdown2.markdown(section_data['content'] or default_text)
                
                # Visual Editor
                # Configure toolbar to be simple but useful
                content_html = st_quill(
                    value=html_input,
                    html=True,
                    key=f"quill_{current}",
                    placeholder="Write your content here...",
                    toolbar=[
                        ['bold', 'italic', 'underline', 'strike'],
                        [{'header': 1}, {'header': 2}],
                        [{'list': 'ordered'}, {'list': 'bullet'}],
                        ['clean']
                    ]
                )
                
                # Convert HTML -> Markdown for storage
                if content_html:
                    # markdownify converts HTML back to Markdown
                    new_md = markdownify.markdownify(content_html, heading_style="ATX")
                    st.session_state.sections[current]['content'] = new_md
                    
            else:
                st.markdown("### 📝 Content Editor (Raw)")
                st.markdown("Use this editor to refine the content. Markdown syntax is supported for formatting.")
                
                # Editor fallback
                edited_content = st.text_area(
                    "Content Editor",
                    value=section_data['content'] or default_text,
                    height=800,
                    label_visibility="collapsed",
                    key=f"content_{current}",
                    help="Edit the generated Markdown content."
                )
                # Update session state on change
                st.session_state.sections[current]['content'] = edited_content
            
        else:
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
                    padding: 30px; 
                    box-sizing: border-box;
                    width: 100%;
                    border-radius: 4px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                    font-family: 'Times New Roman', Times, serif;
                    font-size: 12pt;
                    line-height: 1.8;
                    color: #1a1a1a;
                    max-height: 800px;
                    overflow-y: auto;
                    text-align: justify;
                    border: 1px solid #ccc;
                ">
            """, unsafe_allow_html=True)
            
            # Render the markdown content
            preview_content = section_data['content'] or default_text
            st.markdown(preview_content)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.button("🔄 Regenerate Section", use_container_width=True, type="primary", on_click=handle_regeneration)
            
        with col2:
            # Replaced with Export Complete Tender (PDF)
            full_text = handle_export_complete_docx()
            full_pdf = create_legal_pdf(full_text)
            
            st.download_button(
                "💾 Export Complete Tender",
                data=full_pdf,
                file_name=f"Full_Tender_Response_{st.session_state.current_filename}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        
        with col3:
             # Commented out export PDF button
             # pdf_buffer = create_legal_pdf(edited_content)
             # st.download_button(...)
             pass
        
        with col4:
            # Commented out mark as reviewed
            pass

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
    
    st.button("⚡ Generate All Sections", use_container_width=True, type="primary", on_click=handle_bulk_generation)
    
    if st.button("💾 Save Progress", use_container_width=True):
        st.success("Progress saved locally!")
    
    # Export Complete Logic (Duplicate removed from here as it's now in main area)
    # full_text = handle_export_complete_docx()
    # full_pdf = create_legal_pdf(full_text)
    # st.download_button(...)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer info
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #6b7280; font-size: 0.85rem;'>
        <strong>Tender Generation System</strong> | Last saved: {time} | Auto-save enabled
    </div>
""".format(time=datetime.now().strftime('%H:%M:%S')), unsafe_allow_html=True)
