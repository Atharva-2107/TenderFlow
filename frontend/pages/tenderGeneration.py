# import streamlit as st
# import pandas as pd
# from datetime import datetime, timedelta
# import time

# # -----------------------------------------------------------------------------
# # 1. PAGE CONFIG & STYLING
# # -----------------------------------------------------------------------------
# st.set_page_config(
#     page_title="TenderFlow | Enterprise RAG Platform",
#     page_icon="🏗️",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# st.markdown("""
#     <style>
#     .main { background-color: #f8f9fa; font-family: 'Inter', sans-serif; }
    
#     .top-bar {
#         background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
#         padding: 1.2rem 2rem;
#         border-radius: 12px;
#         margin-bottom: 2rem;
#         color: white;
#         display: flex;
#         justify-content: space-between;
#         align-items: center;
#     }

#     /* Role Selection Card Styling */
#     .role-card {
#         background-color: white;
#         padding: 30px;
#         border-radius: 15px;
#         border: 1px solid #e2e8f0;
#         text-align: center;
#         transition: transform 0.2s;
#         cursor: pointer;
#     }
#     .role-card:hover {
#         transform: translateY(-5px);
#         border-color: #3b82f6;
#         box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
#     }

#     .step-item {
#         flex: 1;
#         text-align: center;
#         padding: 10px;
#         border-bottom: 4px solid #e2e8f0;
#         color: #94a3b8;
#         font-weight: 600;
#     }
#     .step-active { border-bottom: 4px solid #3b82f6; color: #1e293b; }
#     .step-complete { border-bottom: 4px solid #10b981; color: #10b981; }

#     .guide-box {
#         background-color: #f0f7ff; 
#         padding: 20px; 
#         border-left: 5px solid #3b82f6; 
#         border-radius: 8px; 
#         margin-bottom: 20px;
#     }
#     </style>
# """, unsafe_allow_html=True)

# # -----------------------------------------------------------------------------
# # 2. SESSION STATE
# # -----------------------------------------------------------------------------
# if 'user_role' not in st.session_state:
#     st.session_state.user_role = None  # Start with no role selected

# if 'step_index' not in st.session_state:
#     st.session_state.step_index = 0

# def set_role(role):
#     st.session_state.user_role = role
#     st.session_state.step_index = 0

# def next_step():
#     st.session_state.step_index += 1

# def prev_step():
#     st.session_state.step_index -= 1

# # -----------------------------------------------------------------------------
# # 3. LANDING PAGE: ROLE SELECTION
# # -----------------------------------------------------------------------------
# if st.session_state.user_role is None:
#     st.markdown("<br><br>", unsafe_allow_html=True)
#     st.markdown("<h1 style='text-align: center;'>Welcome to TenderFlow AI</h1>", unsafe_allow_html=True)
#     st.markdown("<p style='text-align: center; color: #64748b;'>Select your workspace to begin</p>", unsafe_allow_html=True)
#     st.markdown("<br>", unsafe_allow_html=True)

#     col_a, col_b, col_c, col_d = st.columns([1, 2, 2, 1])
    
#     with col_b:
#         st.markdown('<div class="role-card">', unsafe_allow_html=True)
#         st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
#         st.markdown("### I am an Issuer")
#         st.caption("I want to create a tender and find the best contractors.")
#         if st.button("Enter Client Workspace", key="btn_issuer", use_container_width=True):
#             set_role("Issuer")
#             st.rerun()
#         st.markdown('</div>', unsafe_allow_html=True)

#     with col_c:
#         st.markdown('<div class="role-card">', unsafe_allow_html=True)
#         st.image("https://cdn-icons-png.flaticon.com/512/3281/3281289.png", width=80)
#         st.markdown("### I am a Bidder")
#         st.caption("I want to analyze tenders and submit winning bids.")
#         if st.button("Enter Contractor Workspace", key="btn_bidder", use_container_width=True):
#             set_role("Bidder")
#             st.rerun()
#         st.markdown('</div>', unsafe_allow_html=True)

# # -----------------------------------------------------------------------------
# # 4. WORKSPACE: ISSUER OR BIDDER
# # -----------------------------------------------------------------------------
# else:
#     # Sidebar remains for secondary info
#     with st.sidebar:
#         st.image("https://cdn-icons-png.flaticon.com/512/2910/2910795.png", width=40)
#         st.markdown("### TenderFlow Pro")
#         st.markdown("---")
#         st.write(f"**Mode:** {st.session_state.user_role}")
#         if st.button("🔄 Switch Role / Exit"):
#             st.session_state.user_role = None
#             st.rerun()

#     # Define Workflow Steps
#     issuer_steps = ["1. Project Details", "2. Technical Scope", "3. Financials (BOQ)", "4. Publish"]
#     bidder_steps = ["1. Upload Tender", "2. AI Summary", "3. Gap Analysis", "4. Submit Bid"]
#     current_steps = issuer_steps if st.session_state.user_role == "Issuer" else bidder_steps

#     # Progress Tracker
#     step_cols = st.columns(len(current_steps))
#     for i, s_label in enumerate(current_steps):
#         is_active = "step-active" if i == st.session_state.step_index else ""
#         is_complete = "step-complete" if i < st.session_state.step_index else ""
#         step_cols[i].markdown(f"""<div class="step-item {is_active} {is_complete}">{s_label}</div>""", unsafe_allow_html=True)

#     st.markdown("<br>", unsafe_allow_html=True)

#     # Header Bar
#     bar_color = "#3b82f6" if st.session_state.user_role == "Issuer" else "#10b981"
#     st.markdown(f"""
#         <div class="top-bar" style="background: {bar_color};">
#             <h1>{current_steps[st.session_state.step_index]}</h1>
#             <div style="font-weight: 500;">Role: {st.session_state.user_role}</div>
#         </div>
#     """, unsafe_allow_html=True)

#     # --- ISSUER LOGIC ---
#     if st.session_state.user_role == "Issuer":
#         if st.session_state.step_index == 0:
#             st.subheader("General Information")
#             st.text_input("Project Name", placeholder="e.g. Mumbai Metro Phase II")
#             st.date_input("Submission Deadline")

#         elif st.session_state.step_index == 1:
#             st.markdown("""
#                 <div class="guide-box">
#                     <h4 style="margin-top:0; color: #1e3a8a;">📝 How to describe your requirements</h4>
#                     <ul style="font-size: 0.9rem; color: #1e40af; line-height: 1.6;">
#                         <li><b>🏗️ Physical Scale:</b> Dimensions, floors, or volume of work.</li>
#                         <li><b>📍 Exact Location:</b> City and site conditions.</li>
#                         <li><b>💎 Target Quality:</b> Define standards (e.g., "IS Code 456").</li>
#                         <li><b>💰 Budget & Timeline:</b> Project value and deadline.</li>
#                         <li><b>🛠️ Tech & Materials:</b> Must-haves like "M40 Concrete".</li>
#                         <li><b>📜 Bidder Profile:</b> Min. experience required.</li>
#                     </ul>
#                 </div>
#             """, unsafe_allow_html=True)
#             st.text_area("Detailed Project Description", height=200, placeholder="Enter details based on the guide above...")

#         elif st.session_state.step_index == 2:
#             st.subheader("Financial Component Builder")
#             df = pd.DataFrame([{"Item": "Civil Works", "Qty": 1, "Rate": 10000}])
#             st.data_editor(df, num_rows="dynamic", use_container_width=True)

#         elif st.session_state.step_index == 3:
#             st.success("Tender Ready!")
#             st.button("Download Professional PDF")

#     # --- BIDDER LOGIC ---
#     else:
#         if st.session_state.step_index == 0:
#             st.subheader("Upload Client Tender")
#             st.file_uploader("Upload PDF")
#         elif st.session_state.step_index == 1:
#             st.info("AI Analysis will be displayed here.")
#         # ... and so on

#     # --- FOOTER NAVIGATION ---
#     st.markdown("---")
#     f_col1, f_col2, f_col3 = st.columns([1, 4, 1])
#     with f_col1:
#         if st.session_state.step_index > 0:
#             st.button("⬅️ Back", on_click=prev_step, use_container_width=True)
#     with f_col3:
#         if st.session_state.step_index < len(current_steps) - 1:
#             st.button("Save & Next ➡️", on_click=next_step, type="primary", use_container_width=True)
#         else:
#             if st.button("Finish 🚀", type="primary", use_container_width=True):
#                 st.balloons()

import streamlit as st
from datetime import datetime, timedelta
# from PyPDF2 import PdfReader # Removed local processing
import json
import requests

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
        background-color: #f0f9ff;
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

    def create_pdf(text_content):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        text = c.beginText(40, 750)
        text.setFont("Helvetica", 12)
        
        for line in text_content.split('\n'):
            if len(line) > 90: 
                line = line[:90] + "..."
            text.textLine(line)
            if text.getY() < 50:
                 c.drawText(text)
                 c.showPage()
                 text = c.beginText(40, 750)
                 text.setFont("Helvetica", 12)
        c.drawText(text)
        c.save()
        buffer.seek(0)
        return buffer

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
        
        # Editable content
        edited_content = st.text_area(
            "Generated Content",
            value=section_data['content'] or default_text,
            height=500,
            key=f"content_{current}",
            help="Edit the generated content as needed. Locked citations cannot be modified."
        )
        
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
             # Generate PDF on the fly
             pdf_buffer = create_pdf(edited_content)
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
    full_pdf = create_pdf(full_text)
    
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
