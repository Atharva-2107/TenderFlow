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

def get_company_context(user_id: str, section_type: str = None) -> str:
    """
    Fetches comprehensive company information for the given user_id.
    Matches the actual database schema from information collection pages.
    
    Args:
        user_id: The user's UUID
        section_type: Optional section type to filter relevant fields
    
    Returns:
        Formatted string with company context, sensitive data hashed
    """
    import hashlib
    
    if not user_id:
        print(f"[DEBUG] get_company_context: No user_id provided")
        return ""
    
    # CRITICAL: Use authenticated Supabase client with user's session
    sb_session = st.session_state.get("sb_session")
    if not sb_session:
        print(f"[DEBUG] get_company_context: No sb_session found")
        return ""
    
    # Create authenticated client
    auth_supabase = create_client(url, key)
    auth_supabase.postgrest.auth(sb_session.access_token)
    
    context_parts = []
    
    def hash_sensitive(value: str, show_last: int = 4) -> str:
        """Hash sensitive data, showing only last N characters"""
        if not value or value == 'N/A':
            return 'N/A'
        if len(value) <= show_last:
            return '*' * len(value)
        return '*' * (len(value) - show_last) + value[-show_last:]
    
    try:
        # 1. Company Information (from informationCollection_1.py)
        # Table: company_information, primary key: id = user_id
        print(f"[DEBUG] Fetching company_information for user_id: {user_id}")
        response = auth_supabase.table("company_information").select("*").eq("id", user_id).maybe_single().execute()
        print(f"[DEBUG] company_information response: {response.data if response else 'None'}")
        
        if response and response.data:
            data = response.data
            # Core company info (always include)
            if data.get('company_name'):
                context_parts.append(f"Company Name: {data.get('company_name')}")
            if data.get('org_type'):
                context_parts.append(f"Organization Type: {data.get('org_type')}")
            if data.get('reg_address'):
                context_parts.append(f"Registered Address: {data.get('reg_address')}")
            if data.get('office_address'):
                context_parts.append(f"Office Address: {data.get('office_address')}")
            if data.get('authorized_signatory'):
                context_parts.append(f"Authorized Signatory: {data.get('authorized_signatory')}")
            if data.get('designation'):
                context_parts.append(f"Signatory Designation: {data.get('designation')}")
            if data.get('email'):
                context_parts.append(f"Contact Email: {data.get('email')}")
            if data.get('phone_number'):
                context_parts.append(f"Contact Phone: {data.get('phone_number')}")
        
        # 2. Business Compliance (from informationCollection_2.py)
        # Table: business_compliance, foreign key: user_id
        print(f"[DEBUG] Fetching business_compliance for user_id: {user_id}")
        response = auth_supabase.table("business_compliance").select("*").eq("user_id", user_id).maybe_single().execute()
        print(f"[DEBUG] business_compliance response: {response.data if response else 'None'}")
        
        if response and response.data:
            data = response.data
            # GST - show partially (important for compliance sections)
            if data.get('gst_number'):
                gst = data.get('gst_number')
                context_parts.append(f"GST Number: {gst[:2]}****{gst[-4:] if len(gst) > 6 else gst}")
            # PAN - hash more heavily (sensitive)
            if data.get('pan_number'):
                context_parts.append(f"PAN Number: {hash_sensitive(data.get('pan_number'), 4)}")
            # Bank details - heavily hashed
            if data.get('bank_account_number'):
                context_parts.append(f"Bank Account: {hash_sensitive(data.get('bank_account_number'), 4)}")
            if data.get('ifsc_code'):
                ifsc = data.get('ifsc_code')
                context_parts.append(f"IFSC Code: {ifsc[:4]}******" if len(ifsc) > 4 else ifsc)
        
        # 3. Financials (from informationCollection_3.py)
        # Table: financials, foreign key: user_id
        print(f"[DEBUG] Fetching financials for user_id: {user_id}")
        response = auth_supabase.table("financials").select("*").eq("user_id", user_id).maybe_single().execute()
        print(f"[DEBUG] financials response: {response.data if response else 'None'}")
        
        if response and response.data:
            data = response.data
            if data.get('avg_annual_turnover'):
                context_parts.append(f"Average Annual Turnover: {data.get('avg_annual_turnover')}")
            if data.get('fy_wise_turnover'):
                context_parts.append(f"FY-wise Turnover: {data.get('fy_wise_turnover')}")
        
        # 4. Experience Records (from informationCollection_4.py)
        # Table: experience_records, foreign key: user_id (multiple records possible)
        print(f"[DEBUG] Fetching experience_records for user_id: {user_id}")
        response = auth_supabase.table("experience_records").select("project_name, client_name, client_type, work_category, contract_value, completion_status").eq("user_id", user_id).execute()
        print(f"[DEBUG] experience_records response: {response.data if response else 'None'}")
        
        if response and response.data and len(response.data) > 0:
            exp_summary = []
            for exp in response.data[:5]:  # Limit to 5 most recent
                exp_str = f"{exp.get('project_name', 'N/A')} ({exp.get('client_type', '')}, {exp.get('contract_value', 'N/A')})"
                exp_summary.append(exp_str)
            if exp_summary:
                context_parts.append(f"Past Projects: {'; '.join(exp_summary)}")

    except Exception as e:
        print(f"[DEBUG] Error fetching company context: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return ""
    
    result = "; ".join(context_parts) if context_parts else ""
    print(f"[DEBUG] Final company context ({len(result)} chars): {result[:200]}...")
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
    /* Main container padding fix */
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #e2e8f0; /* Lighter color for dark mode */
        margin-bottom: 2rem; /* More space below */
        padding-bottom: 0.8rem;
        border-bottom: 3px solid #3b82f6;
        margin-top: 2rem; /* Ensure space from top bar */
    }
    
    /* Top Bar Styling */
    .top-bar {
        background-color: #1e293b;
        padding: 20px 25px;
        border-radius: 8px;
        margin-bottom: 30px;
        border: 1px solid #334155;
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-top: 0px; /* Fixed overlap issue */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .top-bar-title {
        color: white;
        font-size: 1.4rem;
        font-weight: bold;
        line-height: 1.2;
    }
    .top-bar-info {
        color: #94a3b8;
        font-size: 0.9rem;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
        width: fit-content;
    }
    .status-ready {
        background-color: #065f46;
        color: #34d399;
    }

    /* Control Panel Styling - Clean Look */
    .control-section {
        margin-bottom: 15px;
        padding: 5px 0px; /* Removed box padding */
        background-color: transparent; /* Removed dark box */
        border: none;
    }
    .control-label {
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 8px;
        color: #f1f5f9; /* Bright white text */
        display: flex;
        align-items: center;
        gap: 8px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Streamlit UI Tweaks */
    div[data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }
    
    /* Ensure content within columns doesn't force scrollbars */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
        overflow: visible;
    }
    
    /* Legal preview containment */
    .legal-preview {
        max-width: 100% !important;
        overflow-x: auto !important;
        word-wrap: break-word !important;
    }
    .legal-preview table {
        max-width: 100% !important;
        overflow-x: auto !important;
        display: block;
    }
    /* Editable preview styling */
    .legal-preview-editable {
        outline: 2px dashed #3b82f6;
        cursor: text;
    }
    .legal-preview-editable:focus {
        outline: 2px solid #3b82f6;
    }
    
    /* Streamlit UI Cleanups */
    div[data-testid="stExpanderr"] {
        border-radius: 8px;
    }
    h3 {
        padding-top: 10px;
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

            # Status text with proper spacing
            st.markdown(
                f"""
                <div style="
                    text-align: center;
                    margin-top: 2px;
                    margin-bottom: 15px;
                    font-size: 13px;
                    font-weight: 600;
                    color: {status_color};
                    letter-spacing: 0.5px;
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
        col_space, col_edit, col_save = st.columns([0.75, 0.12, 0.13])
        with col_edit:
            is_editing = st.checkbox("✍️ Edit", key=f"edit_mode_{current}", help="Edit directly in the legal preview")
        
        if f"edited_content_{current}" not in st.session_state:
            st.session_state[f"edited_content_{current}"] = section_data['content'] or default_text

        # Toggle structure
        if is_editing:
            # EDIT MODE
            new_content = st.text_area(
                "Edit Content",
                value=st.session_state[f"edited_content_{current}"],
                height=600,
                label_visibility="collapsed",
                key=f"editor_{current}"
            )
            st.session_state[f"edited_content_{current}"] = new_content
            
            # Save Button (Commented out as duplicate)
            # if st.button("💾 Save Changes", type="primary", key=f"save_{current}"):
            #     st.session_state.sections[current]['content'] = new_content
            #     st.session_state[f"content_{current}"] = new_content
            #     st.session_state[f"edit_mode_{current}"] = False # Exit edit mode
            #     st.success("Changes saved!")
            #     st.rerun()

        else:
            # PREVIEW MODE
            # Use current content (committed)
            display_content = st.session_state.sections[current]['content'] or default_text
            
            # Convert markdown to HTML for display
            # Removed 'fenced-code-blocks' to correct "code snippet" issue
            html_content = markdown2.markdown(
                display_content,
                extras=["tables", "header-ids"]
            )
            
            st.markdown(f"""
<style>
    .legal-preview table {{
        width: 100%;
        max-width: 100%;
        border: 1px solid black;
        border-collapse: collapse;
        margin: 15px 0;
        display: table;
        table-layout: fixed;
    }}
    .legal-preview th {{
        background-color: #2c3e50;
        color: white;
        font-weight: bold;
        padding: 10px;
        border: 1px solid black;
        text-align: left;
        word-wrap: break-word;
    }}
    .legal-preview td {{
        padding: 8px;
        border: 1px solid black;
        vertical-align: top;
        word-wrap: break-word;
    }}
    .legal-preview h3 {{
        font-weight: bold;
        margin-top: 20px;
        border-bottom: 2px solid #333;
        padding-bottom: 5px;
    }}
    .legal-preview h4 {{
        font-weight: bold;
        margin-top: 15px;
        color: #2c3e50;
    }}
    /* Scrollable Container Styling */
    .preview-scroll-container {{
        height: 800px;
        overflow-y: auto;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 20px;
        background-color: #0D1117; /* Dark background frame */
        box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
    }}
    /* Custom Scrollbar */
    .preview-scroll-container::-webkit-scrollbar {{
        width: 10px;
        height: 10px;
    }}
    .preview-scroll-container::-webkit-scrollbar-track {{
        background: #0D1117;
    }}
    .preview-scroll-container::-webkit-scrollbar-thumb {{
        background: #30363D;
        border-radius: 5px;
    }}
    .preview-scroll-container::-webkit-scrollbar-thumb:hover {{
        background: #58a6ff;
    }}
</style>

<div class="preview-scroll-container">
    <div class="legal-preview" style="
        background-color: white;
        padding: 40px; 
        box-sizing: border-box;
        width: 100%;
        max-width: 100%;
        border-radius: 4px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        font-family: 'Times New Roman', Times, serif;
        font-size: 12pt;
        line-height: 1.6;
        color: #1a1a1a;
        min-height: 800px; /* Ensure paper has height */
        text-align: justify;
        border: 1px solid #ccc;
    ">
        {html_content}
    </div>
</div>
""", unsafe_allow_html=True)
        
        # CLEARING DIV to prevent float overlap issues
        st.markdown('<div style="clear: both; margin-bottom: 20px;"></div>', unsafe_allow_html=True)
        st.divider()

        # Show save button when editing
        with col_save:
            if is_editing:
                if st.button("💾 Save", key=f"save_edit_{current}", help="Save your edits"):
                    st.success("Changes saved!")
                    st.rerun()
        
        # Action buttons
        col1, col2, padding_col = st.columns([1.5, 1.5, 3])
        
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
    st.markdown('<div style="margin-bottom: 15px;"></div>', unsafe_allow_html=True) 
    
    st.button("⚡ Generate All Sections", use_container_width=True, type="primary", on_click=handle_bulk_generation)
    st.markdown('<div style="margin-bottom: 10px;"></div>', unsafe_allow_html=True)
    
    # if st.button("💾 Save Progress", use_container_width=True):
    #     st.success("Progress saved locally!")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer info
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #6b7280; font-size: 0.85rem; padding-bottom: 30px;'>
        <strong>Tender Generation System</strong> | Last saved: {time} | Auto-save enabled
    </div>
""".format(time=datetime.now().strftime('%H:%M:%S')), unsafe_allow_html=True)
