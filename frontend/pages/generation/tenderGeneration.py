import streamlit as st
from datetime import datetime, timedelta
from PyPDF2 import PdfReader
import json

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

if 'pdf_text' not in st.session_state:
    st.session_state.pdf_text = ""

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
        
        if uploaded_file and not st.session_state.pdf_uploaded:
            try:
                pdf_reader = PdfReader(uploaded_file)
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text()
                st.session_state.pdf_text = text_content
                st.session_state.pdf_uploaded = True
                
                # Auto-update section statuses
                st.session_state.sections['Eligibility Response']['status'] = '✅'
                st.session_state.sections['Technical Proposal']['status'] = '✅'
                st.session_state.sections['Eligibility Response']['clauses'] = 12
                st.session_state.sections['Technical Proposal']['clauses'] = 8
                
                st.success("✅ Uploaded!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
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
                    font-size: 12px;
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
        # Sample content based on section
        if current == 'Eligibility Response':
            default_content = f"""1. ORGANIZATIONAL ELIGIBILITY

The Bidder hereby declares and affirms compliance with all eligibility criteria as stipulated in Clause 2 of the Request for Proposal (RFP) document.

1.1 Legal Status and Registration
The Bidder is a legally constituted entity registered under the applicable laws of India, with valid registration certificates attached as Annexure A.

1.2 Financial Capability
The Bidder possesses the requisite financial capability as evidenced by:
- Average annual turnover of INR 50 Crores or more during the last three financial years (FY 2021-22, 2022-23, 2023-24)
- Audited financial statements attached as Annexure B
- Net worth certificate from Chartered Accountant attached as Annexure C

1.3 Technical Competence
The Bidder has successfully completed similar projects as per the requirements:
- Minimum 3 projects of similar nature and scope in the last 5 years
- Project completion certificates attached as Annexure D
- Total project value exceeding INR 30 Crores

[LOCKED CITATION: As per RFP Clause 2.3 - "Bidder must demonstrate experience in executing minimum three projects of similar nature valued at INR 10 Crores or more each"]

1.4 Compliance Declarations
The Bidder affirms that:
- No proceedings for insolvency or bankruptcy are pending
- Not blacklisted by any Government department or PSU
- All statutory compliances including GST, PF, ESI are up to date
"""
        elif current == 'Technical Proposal':
            default_content = f"""TECHNICAL PROPOSAL

1. UNDERSTANDING OF PROJECT SCOPE

The Bidder acknowledges comprehensive understanding of the project requirements as outlined in the RFP. This proposal details our technical approach, methodology, and implementation strategy.

1.1 Project Objectives
We understand the key objectives include:
- Modernization of existing IT infrastructure
- Implementation of scalable and secure systems
- Minimal disruption to ongoing operations
- Compliance with Government IT standards

2. TECHNICAL APPROACH AND METHODOLOGY

2.1 Phase-wise Implementation
Phase 1 (Month 1-3): Assessment and Planning
- Infrastructure audit and gap analysis
- Detailed project planning and resource allocation
- Risk assessment and mitigation planning

[LOCKED CITATION: As per RFP Clause 3.2 - "Implementation shall be completed in phases with minimal operational disruption"]

Phase 2 (Month 4-8): Core Implementation
- Hardware procurement and installation
- Software deployment and configuration
- Integration with existing systems

Phase 3 (Month 9-12): Testing and Handover
- Comprehensive testing protocols
- User training and documentation
- Final handover and warranty support

2.2 Resource Deployment
- Dedicated project manager with PMP certification
- Team of 15+ technical specialists
- 24/7 support desk during implementation
"""
        else:
            default_content = f"""[Content for {current} section will be generated based on uploaded tender document]

This section will include all relevant information extracted from clauses pertaining to {current.lower()}.

Please upload a tender document to generate detailed content."""
        
        # Editable content
        edited_content = st.text_area(
            "Generated Content",
            value=section_data['content'] or default_content,
            height=400,
            key=f"content_{current}",
            help="Edit the generated content as needed. Locked citations cannot be modified."
        )
        
        st.session_state.sections[current]['content'] = edited_content
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔄 Regenerate Section", use_container_width=True):
                st.info("Regenerating section with updated parameters...")
                
        with col2:
            if st.button("📄 Export DOCX", use_container_width=True):
                st.download_button(
                    "⬇ Download",
                    data=edited_content,
                    file_name=f"{current.replace(' ', '_')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        
        with col3:
            if st.button("📑 Export PDF", use_container_width=True):
                st.info("PDF export functionality")
        
        with col4:
            if st.button("✅ Mark as Reviewed", use_container_width=True):
                st.session_state.sections[current]['status'] = '✅'
                st.success("Section marked as reviewed!")
                st.rerun()
    else:
        st.warning("⚠️ Please upload a tender document from the left panel to generate content")

# RIGHT PANEL - Controls
with right_panel:
    # st.markdown('<div class="control-panel">', unsafe_allow_html=True)
    
    st.markdown("### ⚙️ Generation Controls")
    
    # Tone selector
    st.markdown('<div class="control-section">', unsafe_allow_html=True)
    st.markdown('<div class="control-label">📝 Tone Style</div>', unsafe_allow_html=True)
    tone = st.radio(
        "Tone",
        ["Formal", "Ultra-Formal"],
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Jurisdiction style
    st.markdown('<div class="control-section">', unsafe_allow_html=True)
    st.markdown('<div class="control-label">🏛️ Jurisdiction</div>', unsafe_allow_html=True)
    jurisdiction = st.radio(
        "Jurisdiction",
        ["Government PSU", "Private Sector"],
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Strict compliance toggle
    st.markdown('<div class="control-section">', unsafe_allow_html=True)
    st.markdown('<div class="control-label">⚖️ Compliance Mode</div>', unsafe_allow_html=True)
    strict_compliance = st.toggle(
        "Strict compliance only",
        value=True,
        help="Only include clauses with strict compliance requirements"
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
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="control-section">', unsafe_allow_html=True)
    st.markdown('<div class="control-label">🔍 Content Depth</div>', unsafe_allow_html=True)
    content_depth = st.select_slider(
        "Depth",
        options=["Concise", "Standard", "Comprehensive"],
        value="Standard",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Bulk actions
    st.markdown("### 🚀 Bulk Actions")
    
    if st.button("📥 Generate All Sections", use_container_width=True, type="primary"):
        st.info("Generating all sections...")
    
    if st.button("💾 Save Progress", use_container_width=True):
        st.success("Progress saved!")
    
    if st.button("📤 Export Complete Tender", use_container_width=True):
        st.info("Exporting complete document...")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer info
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #6b7280; font-size: 0.85rem;'>
        <strong>Tender Generation System</strong> | Last saved: {time} | Auto-save enabled
    </div>
""".format(time=datetime.now().strftime('%H:%M:%S')), unsafe_allow_html=True)