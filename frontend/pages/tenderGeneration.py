import streamlit as st
from datetime import datetime, timedelta
import time
import requests
import markdown2
from xhtml2pdf import pisa
from io import BytesIO
import os
import base64
from pathlib import Path
from supabase import create_client, Client
from utils.auth import can_access

# UI HELPERS
def get_base64_of_bin_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


# THEME CONSTANTS (FROM 2nd CODE)
THEME_PURPLE = "#a855f7"
THEME_INDIGO = "#1a1c4b"
THEME_DARK = "#0f111a"
THEME_WHITE = "#ffffff"
BG_GRADIENT = "radial-gradient(circle at 20% 30%, #1a1c4b 0%, #0f111a 100%)"


# ACCESS CONTROL (PRESERVED)
if not can_access("tender_generation"):
    st.markdown(
        f'<div style="color: {THEME_PURPLE}; padding: 20px; border: 1px solid {THEME_PURPLE}; border-radius: 10px;">You are not authorized to access this page.</div>',
        unsafe_allow_html=True
    )
    st.stop()


# BACKEND CONFIG (PRESERVED)
API_BASE_URL = "http://localhost:8000"

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

# Initialize Supabase Client (PRESERVED)
if url and key:
    supabase: Client = create_client(url, key)

    current_session = st.session_state.get("sb_session")

    try:
        client_session = supabase.auth.get_session()
        if client_session:
            st.session_state.sb_session = client_session
            current_session = client_session
    except Exception as e:
        print(f"Session Error: {e}")

    if current_session:
        user_id = current_session.user.id
    else:
        user_id = None
else:
    user_id = None


# LOGIC FUNCTIONS (PRESERVED - from 1st code)
def save_tender_to_db(user_id, project_name, content, section_type, category="Any", pdf_bytes=None):
    if not user_id:
        return False

    try:
        pdf_url = None
        if pdf_bytes:
            try:
                safe_proj = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
                safe_sec = "".join(c for c in section_type if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
                timestamp = int(time.time())
                file_path = f"{user_id}/{safe_proj}_{safe_sec}_{timestamp}.pdf"

                supabase.storage.from_("generated-tenders").upload(
                    file_path,
                    pdf_bytes.getvalue() if hasattr(pdf_bytes, 'getvalue') else pdf_bytes,
                    {"content-type": "application/pdf", "upsert": "true"}
                )

                pdf_url = supabase.storage.from_("generated-tenders").get_public_url(file_path)
            except Exception as e:
                print(f"PDF Upload Error: {e}")

        data = {
            "user_id": user_id,
            "project_name": project_name,
            "content": content,
            "section_type": section_type,
            "category": category,
            "created_at": datetime.now().isoformat()
        }

        if pdf_url:
            data["pdf_url"] = pdf_url

        supabase.table("generated_tenders").insert(data).execute()
        return True

    except Exception as e:
        print(f"DB Save Error: {e}")
        return False


def get_company_context(user_id: str, section_type: str = None) -> str:
    import hashlib

    if not user_id:
        print(f"[DEBUG] get_company_context: No user_id provided")
        return ""

    sb_session = st.session_state.get("sb_session")
    if not sb_session:
        print(f"[DEBUG] get_company_context: No sb_session found")
        return ""

    auth_supabase = create_client(url, key)
    auth_supabase.postgrest.auth(sb_session.access_token)

    context_parts = []

    def hash_sensitive(value: str, show_last: int = 4) -> str:
        if not value or value == 'N/A':
            return 'N/A'
        if len(value) <= show_last:
            return '*' * len(value)
        return '*' * (len(value) - show_last) + value[-show_last:]

    try:
        # company_information
        response = auth_supabase.table("company_information").select("*").eq("id", user_id).maybe_single().execute()
        if response and response.data:
            data = response.data
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

        # business_compliance
        response = auth_supabase.table("business_compliance").select("*").eq("user_id", user_id).maybe_single().execute()
        if response and response.data:
            data = response.data
            if data.get('gst_number'):
                gst = data.get('gst_number')
                context_parts.append(f"GST Number: {gst[:2]}****{gst[-4:] if len(gst) > 6 else gst}")
            if data.get('pan_number'):
                context_parts.append(f"PAN Number: {hash_sensitive(data.get('pan_number'), 4)}")
            if data.get('bank_account_number'):
                context_parts.append(f"Bank Account: {hash_sensitive(data.get('bank_account_number'), 4)}")
            if data.get('ifsc_code'):
                ifsc = data.get('ifsc_code')
                context_parts.append(f"IFSC Code: {ifsc[:4]}******" if len(ifsc) > 4 else ifsc)

        # financials
        response = auth_supabase.table("financials").select("*").eq("user_id", user_id).maybe_single().execute()
        if response and response.data:
            data = response.data
            if data.get('avg_annual_turnover'):
                context_parts.append(f"Average Annual Turnover: {data.get('avg_annual_turnover')}")
            if data.get('fy_wise_turnover'):
                context_parts.append(f"FY-wise Turnover: {data.get('fy_wise_turnover')}")

        # experience_records
        response = auth_supabase.table("experience_records").select(
            "project_name, client_name, client_type, work_category, contract_value, completion_status"
        ).eq("user_id", user_id).execute()

        if response and response.data and len(response.data) > 0:
            exp_summary = []
            for exp in response.data[:5]:
                exp_str = f"{exp.get('project_name', 'N/A')} ({exp.get('client_type', '')}, {exp.get('contract_value', 'N/A')})"
                exp_summary.append(exp_str)
            if exp_summary:
                context_parts.append(f"Past Projects: {'; '.join(exp_summary)}")

    except Exception as e:
        print(f"[DEBUG] Error fetching company context: {e}")
        return ""

    return "; ".join(context_parts) if context_parts else ""


def create_legal_pdf(markdown_content):
    css_styles = """
    <style>
        @page { size: A4; margin: 2.5cm 2cm 2.5cm 2cm; }
        body {
            font-family: 'Times New Roman', Times, serif;
            font-size: 12pt;
            line-height: 1.6;
            text-align: justify;
            color: #1a1a1a;
        }

        .eligibility-outline {
            border: 2px dashed rgba(168, 85, 247, 0.55);
            border-radius: 18px;
            padding: 14px;
            background: rgba(168, 85, 247, 0.03);
            box-shadow: 0 0 30px rgba(168, 85, 247, 0.08);
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
        h2 { font-size: 14pt; font-weight: bold; margin-top: 20px; margin-bottom: 10px; color: #2c3e50; }
        h3 { font-size: 12pt; font-weight: bold; margin-top: 15px; margin-bottom: 8px; color: #34495e; }
        p { margin-bottom: 10px; text-indent: 0; }
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
        tr:nth-child(even) { background-color: #f9f9f9; }
        ul, ol { margin-left: 20px; margin-bottom: 10px; }
        li { margin-bottom: 5px; }
        strong { font-weight: bold; }
    </style>
    """

    html_content = markdown2.markdown(
        markdown_content,
        extras=["tables", "header-ids"]
    )

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

    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(full_html, dest=pdf_buffer)

    if pisa_status.err:
        pdf_buffer = BytesIO()
        pdf_buffer.write(markdown_content.encode('utf-8'))

    pdf_buffer.seek(0)
    return pdf_buffer


def create_pdf(text_content):
    return create_legal_pdf(text_content)


# PAGE CONFIG (PRESERVED)
st.set_page_config(
    page_title="Automated Tender Generation",
    page_icon="ÃƒÂ°Ã…Â¸Ã¢â‚¬Å“Ã¢â‚¬Å¾",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# CSS
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

.stApp {{
    background: radial-gradient(circle at 20% 30%, #1a1c4b 0%, #0f111a 100%) !important;
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: {THEME_WHITE};
}}

header, footer {{ visibility: hidden; }}

.block-container {{
    padding-top: 0.5rem !important;
    max-width: 100% !important;
}}

/* Alerts */
.stAlert {{
    background: rgba(168, 85, 247, 0.08);
    border: 1px solid rgba(168,85,247,0.25);
    border-radius: 12px;
    color: white;
}}

/* Buttons */
button[kind="primary"] {{
    background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
    border: none !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px !important;
    transition: opacity 0.15s !important;
}}

button[kind="primary"]:hover {{
    opacity: 0.88 !important;
}}

button[kind="secondary"] {{
    background: rgba(255,255,255,0.06) !important;
    color: rgba(255,255,255,0.85) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}}

button[kind="secondary"]:hover {{
    background: rgba(255,255,255,0.10) !important;
}}

/* Section Navigation Buttons */
div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] button {{
    text-align: left !important;
    justify-content: flex-start !important;
}}

/* Progress Bar */
div[data-baseweb="progress-bar"] > div > div {{
    background: linear-gradient(90deg, #7c3aed, #a855f7) !important;
}}

/* Text Areas */
.stTextArea textarea {{
    background: rgba(255,255,255,0.04) !important;
    color: white !important;
    border: 1px solid rgba(168,85,247,0.35) !important;
    border-radius: 12px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 14px !important;
    line-height: 1.7 !important;
}}

/* File Uploader */
[data-testid="stFileUploadDropzone"] {{
    background: rgba(168,85,247,0.06) !important;
    border: 2px dashed rgba(168,85,247,0.35) !important;
    border-radius: 12px !important;
    color: rgba(255,255,255,0.7) !important;
}}

/* Checkboxes & Toggles */
[data-testid="stCheckbox"] label,
[data-testid="stToggle"] label {{
    color: rgba(255,255,255,0.8) !important;
    font-size: 13px !important;
}}

/* Radio */
.stRadio label {{
    color: rgba(255,255,255,0.75) !important;
    font-size: 13px !important;
}}

/* Select Slider */
[data-testid="stSlider"] div {{
    color: rgba(255,255,255,0.8) !important;
}}

/* Select Box */
.stSelectbox label, .stTextInput label {{
    color: rgba(255,255,255,0.55) !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}

/* Download Button */
[data-testid="stDownloadButton"] > button {{
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: rgba(255,255,255,0.85) !important;
    border-radius: 10px !important;
}}

/* Section Title */
.section-title {{
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #ffffff, #d8b4fe);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 2px;
}}

/* Document Paper */
.document-paper {{
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.07);
    color: rgba(255,255,255,0.92);
    padding: 40px 48px;
    border-radius: 16px;
    min-height: 700px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    line-height: 1.8;
    font-size: 14px;
}}

.document-paper h1, .document-paper h2, .document-paper h3 {{
    color: white;
    margin-top: 1.4em;
}}

.document-paper table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
}}

.document-paper th {{
    background: rgba(168,85,247,0.2);
    color: white;
    padding: 10px 12px;
    text-align: left;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    border: 1px solid rgba(168,85,247,0.25);
}}

.document-paper td {{
    color: rgba(255,255,255,0.8);
    padding: 9px 12px;
    border: 1px solid rgba(255,255,255,0.07);
    font-size: 13px;
}}

.document-paper tr:nth-child(even) td {{
    background: rgba(255,255,255,0.02);
}}

/* Pane Cards */
.pane-section {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 14px;
}}

.pane-label {{
    color: rgba(255,255,255,0.4);
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 10px;
}}

/* Eligibility Outline */
.eligibility-outline {{
    border: 1.5px dashed rgba(168, 85, 247, 0.45);
    border-radius: 12px;
    padding: 8px;
    background: rgba(168, 85, 247, 0.04);
}}
</style>
""", unsafe_allow_html=True)


# SESSION STATE (PRESERVED)
if 'sections' not in st.session_state:
    st.session_state.sections = {
        'Eligibility Response': {'status': 'Ã¢Å¡Â ', 'content': '', 'clauses': 0},
        'Technical Proposal': {'status': 'Ã¢Å¡Â ', 'content': '', 'clauses': 0},
        'Financial Statements': {'status': 'Ã¢ÂÅ’', 'content': '', 'clauses': 0},
        'Declarations & Forms': {'status': 'Ã¢Å“â€¦', 'content': '', 'clauses': 0},
        'Annexures': {'status': 'Ã¢ÂÅ’', 'content': '', 'clauses': 0}
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


# HEADER NAVIGATION
left, center = st.columns([3, 7])

with left:
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
    logo = get_base64_of_bin_file(logo_path)
    if logo:
        st.markdown(f'<img src="data:image/png;base64,{logo}" width="180" style="margin-top:4px">', unsafe_allow_html=True)

with center:
    nav_cols = st.columns([3, 0.5, 0.5, 0.5, 0.5, 0.5])
    with nav_cols[1]:
        if st.button("Ã¢Å Å¾", key="h_dash", help="Dashboard"):
            st.switch_page("app.py")
    with nav_cols[2]:
        if can_access("tender_generation"):
            if st.button("Ã¢Å½Ëœ", key="h_gen", help="Tender Generation"):
                st.switch_page("pages/tenderGeneration.py")
        else:
            st.button("Ã¢Å½Ëœ", key="h_gen_disabled", disabled=True, help="Access restricted")
    with nav_cols[3]:
        if can_access("tender_analysis"):
            if st.button("Ã¢â€”Ë†", key="h_anl", help="Tender Analysis"):
                st.switch_page("pages/tenderAnalyser.py")
        else:
            st.button("Ã¢â€”Ë†", key="h_anl_disabled", disabled=True)
    with nav_cols[4]:
        if can_access("bid_generation"):
            if st.button("Ã¢Å“Â¦", key="h_bid", help="Bid Generation"):
                st.switch_page("pages/bidGeneration.py")
        else:
            st.button("Ã¢Å“Â¦", key="h_bid_disabled", disabled=True)
    with nav_cols[5]:
        if can_access("risk_analysis"):
            if st.button("Ã¢Â¬Ë†", key="h_risk", help="Risk Analysis"):
                st.switch_page("pages/riskAnalysis.py")
        else:
            st.button("Ã¢Â¬Ë†", key="h_risk_disabled", disabled=True)


# TOP BANNER
st.markdown(f"""
<div style="
    display:flex;
    justify-content:space-between;
    align-items:flex-end;
    margin: 14px 0 22px 0;
    padding-bottom: 16px;
    border-bottom: 1px solid rgba(168,85,247,0.25);
">
    <div>
        <h1 class="section-title">Tender Studio</h1>
        <p style="color:rgba(255,255,255,0.5);margin:2px 0 0 0;font-size:13px;">AI-Powered Clause Generation &amp; Response Drafting</p>
        <p style="color:rgba(255,255,255,0.3);margin:4px 0 0 0;font-size:12px;">
            <strong style="color:rgba(168,85,247,0.8)">Deadline:</strong> {st.session_state.tender_config['deadline']}
        </p>
    </div>
    <div style="text-align:right;">
        <div style="color:rgba(255,255,255,0.4);font-size:11px;text-transform:uppercase;letter-spacing:1px;">Authority</div>
        <div style="color:white;font-size:15px;font-weight:600;margin-top:2px;">{st.session_state.tender_config['authority']}</div>
        <div style="
            display:inline-block;
            margin-top:6px;
            padding:5px 12px;
            border:1px solid rgba(168,85,247,0.35);
            border-radius:100px;
            background:rgba(168,85,247,0.1);
            color:rgba(168,85,247,0.9);
            font-size:12px;
            font-weight:700;
        ">{st.session_state.tender_config['status']}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# CALLBACKS (PRESERVED)
def handle_regeneration():
    current = st.session_state.current_section

    if not st.session_state.pdf_uploaded:
        st.error("Please upload a document first.")
        return

    try:
        tone_val = st.session_state.get("gen_tone", "Formal")
        comp_val = st.session_state.get("gen_compliance", True)

        user = st.session_state.get("user")
        user_id_local = getattr(user, 'id', None) or (user.get('id') if isinstance(user, dict) else None)

        company_context = ""
        if user_id_local:
            st.toast("ÃƒÂ°Ã…Â¸Ã¢â‚¬ÂÃ‚Â Fetching company data...")
            company_context = get_company_context(user_id_local)
            if company_context:
                st.toast(f"ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ Context loaded ({len(company_context)} chars)")

        payload = {
            "filename": st.session_state.current_filename,
            "section_type": current,
            "tone": tone_val,
            "compliance_mode": comp_val,
            "company_context": company_context
        }

        gen_resp = requests.post(f"{API_BASE_URL}/generate-section", data=payload)

        if gen_resp.status_code == 200:
            data = gen_resp.json()
            st.session_state.sections[current]['content'] = data['content']
            st.session_state[f"content_{current}"] = data['content']
            st.success("Content Drafted!")
        else:
            st.error(f"Generation failed: {gen_resp.text}")

    except Exception as e:
        st.error(f"API Error: {str(e)}")


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

        user = st.session_state.get("user")
        user_id_local = getattr(user, 'id', None) or (user.get('id') if isinstance(user, dict) else None)
        company_context = get_company_context(user_id_local) if user_id_local else ""

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


# 3-PANE LAYOUT (UI from 2nd code, data/logic from 1st)
left_pane, center_pane, right_pane = st.columns([1, 3.5, 1], gap="large")

# Ã¢â€â‚¬Ã¢â€â‚¬ LEFT PANE Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
with left_pane:
    # Upload Section
    st.markdown('<div class="pane-label">Ã°Å¸â€œÂ¤ Source Document</div>', unsafe_allow_html=True)
    with st.container(border=True):
        uploaded_file = st.file_uploader("Upload RFP / Tender PDF", type=['pdf'], label_visibility="collapsed")

        use_hq_parsing = st.checkbox(
            "High-Quality OCR Parsing",
            value=False,
            help="Uses LlamaParse for tables & scanned docs. Slower."
        )

        if uploaded_file:
            # Reset pdf_uploaded state when a NEW file is selected
            if uploaded_file.name != st.session_state.get("current_filename"):
                st.session_state.pdf_uploaded = False
                st.session_state.current_filename = None
                # Reset section contents for the new document
                for sec_name in st.session_state.sections:
                    st.session_state.sections[sec_name]['content'] = ''
                    st.session_state.sections[sec_name]['clauses'] = 0
                    st.session_state.sections[sec_name]['status'] = 'Ã¢Å¡Â '
                    if f"edited_content_{sec_name}" in st.session_state:
                        del st.session_state[f"edited_content_{sec_name}"]

        if uploaded_file and not st.session_state.pdf_uploaded:
            try:
                with st.spinner("Analyzing document structure..."):
                    files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                    data = {"parsing_mode": "High-Quality" if use_hq_parsing else "Fast"}

                    response = requests.post(
                        f"{API_BASE_URL}/upload-tender",
                        files=files,
                        data=data,
                        timeout=120
                    )

                    if response.status_code == 200:
                        st.session_state.pdf_uploaded = True
                        st.session_state.current_filename = uploaded_file.name

                        st.session_state.sections['Eligibility Response']['status'] = '✅'
                        st.session_state.sections['Technical Proposal']['status'] = '✅'
                        st.session_state.sections['Financial Statements']['status'] = '✅'
                        st.session_state.sections['Declarations & Forms']['status'] = '✅'
                        st.session_state.sections['Annexures']['status'] = '✅'

                        st.session_state.sections['Eligibility Response']['clauses'] = 12
                        st.session_state.sections['Technical Proposal']['clauses'] = 8
                        st.session_state.sections['Financial Statements']['clauses'] = 5
                        st.session_state.sections['Declarations & Forms']['clauses'] = 4
                        st.session_state.sections['Annexures']['clauses'] = 3

                        mode_msg = "OCR" if use_hq_parsing else "Fast"
                        st.success(f"✅ Indexed! Mode: {mode_msg}")
                        st.rerun()
                    else:
                        st.error(f"Upload failed: {response.text}")

            except requests.exceptions.Timeout:
                st.error("⏱️ Timed out. Try Fast mode or a smaller file.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    if st.session_state.pdf_uploaded:
        st.markdown(f'<div style="color:#86efac;font-size:11px;margin-top:4px;">📄 {st.session_state.current_filename}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # Sections
    st.markdown('<div class="pane-label">📑 Sections</div>', unsafe_allow_html=True)

    STATUS_COLORS = {'✅': '#86efac', '⚠': '#fcd34d', '❌': '#f87171'}

    for section_name, section_data in st.session_state.sections.items():
        is_active = section_name == st.session_state.current_section
        status = section_data['status']
        sc = STATUS_COLORS.get(status, 'white')

        if section_name == "Eligibility Response":
            st.markdown('<div class="eligibility-outline">', unsafe_allow_html=True)

        if st.button(
            f"{status} {section_name}",
            key=f"nav_{section_name}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state.current_section = section_name
            st.rerun()

        if section_name == "Eligibility Response":
            st.markdown('</div>', unsafe_allow_html=True)

# ── CENTER PANE ──────────────────────────────────────────────
with center_pane:
    current = st.session_state.current_section
    section_data = st.session_state.sections[current]

    # Toolbar header
    toolbar_left, toolbar_right = st.columns([3, 1])
    with toolbar_left:
        st.markdown(f"""
        <div style="margin-bottom:8px;">
            <h2 style="color:white;font-size:22px;font-weight:700;margin:0;">{current}</h2>
            <p style="color:rgba(255,255,255,0.35);font-size:12px;margin:3px 0 0 0;">
                {'📋 Generated from ' + str(section_data['clauses']) + ' clauses' if section_data['clauses'] > 0 else '⬆ Upload a tender document to enable AI generation'}
            </p>
        </div>""", unsafe_allow_html=True)

    with toolbar_right:
        is_editing = st.toggle("✏️ Edit Mode", value=False, key=f"edit_mode_{current}")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # Content
    default_text = "Click **Generate All Sections** in the right panel to draft this proposal using AI."
    if f"edited_content_{current}" not in st.session_state:
        st.session_state[f"edited_content_{current}"] = section_data['content'] or default_text

    if is_editing:
        new_content = st.text_area(
            "Edit Content",
            value=st.session_state[f"edited_content_{current}"],
            height=680,
            label_visibility="collapsed",
            key=f"editor_{current}"
        )
        st.session_state[f"edited_content_{current}"] = new_content

        save_col1, save_col2 = st.columns([3, 1])
        with save_col2:
            if st.button("Ã°Å¸â€™Â¾ Save Edits", key=f"save_edit_{current}", use_container_width=True, type="primary"):
                st.session_state.sections[current]['content'] = new_content
                st.session_state[f"content_{current}"] = new_content
                st.success("Saved!")
                st.rerun()
    else:
        display_content = st.session_state.sections[current]['content'] or default_text
        html_content = markdown2.markdown(display_content, extras=["tables", "header-ids"])
        st.markdown(f'<div class="document-paper">{html_content}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Action row
    act1, act2 = st.columns(2)
    with act1:
        st.button("Ã°Å¸â€â€ž Regenerate Section", use_container_width=True, type="primary", on_click=handle_regeneration)
    with act2:
        full_text = handle_export_complete_docx()
        full_pdf = create_legal_pdf(full_text)
        st.download_button(
            "Ã°Å¸â€œÂ¥ Export Complete Tender PDF",
            data=full_pdf,
            file_name=f"TenderResponse_{st.session_state.current_filename or 'Draft'}.pdf",
            mime="application/pdf",
            use_container_width=True
        )



# Ã¢â€â‚¬Ã¢â€â‚¬ RIGHT PANE Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
with right_pane:

    st.markdown('<div class="pane-label">Ã¢Å¡â„¢Ã¯Â¸Â Generation Controls</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div style="color:rgba(255,255,255,0.55);font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Tone</div>', unsafe_allow_html=True)
        st.radio("Tone", ["Formal", "Ultra-Formal"], label_visibility="collapsed", key="gen_tone")

        st.markdown('<div style="color:rgba(255,255,255,0.55);font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin:10px 0 6px;">Jurisdiction</div>', unsafe_allow_html=True)
        st.radio("Jurisdiction", ["Government PSU", "Private Sector"], label_visibility="collapsed", key="gen_jurisdiction")

        st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)
        st.toggle("Strict Compliance Mode", value=True, key="gen_compliance")

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="pane-label">Ã°Å¸â€œÅ  Output Settings</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.select_slider("Citation Level", options=["Minimal", "Standard", "Detailed"], value="Standard", key="gen_citation")
        st.select_slider("Content Depth", options=["Concise", "Standard", "Comprehensive"], value="Standard", key="gen_depth")

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="pane-label">Ã°Å¸Å¡â‚¬ Bulk Actions</div>', unsafe_allow_html=True)
    st.button("Ã¢Å¡Â¡ Generate All Sections", use_container_width=True, type="primary", on_click=handle_bulk_generation)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="pane-label">Ã¢ËœÂÃ¯Â¸Â Cloud Save</div>', unsafe_allow_html=True)

    with st.container(border=True):
        category_options = [
            "Any", "Infrastructure", "IT & Technology", "Construction",
            "Supply & Procurement", "Healthcare", "Education",
            "Transport & Logistics", "Energy & Utilities"
        ]
        selected_category = st.selectbox("Category", options=category_options, index=0)
        project_name_input = st.text_input("Project Name", value="New Tender")

        if st.button("Ã°Å¸â€™Â¾ Save to Cloud DB", use_container_width=True):
            current_user = st.session_state.get("user")
            current_user_id = getattr(current_user, 'id', None) or (current_user.get('id') if isinstance(current_user, dict) else None)

            if not current_user_id:
                st.warning("You must be logged in to save.")
            else:
                saved_count = 0
                with st.spinner("Saving..."):
                    for sec_name, sec_data in st.session_state.sections.items():
                        content_to_save = sec_data.get('content', '')
                        if content_to_save:
                            pdf_bytes = create_legal_pdf(content_to_save)
                            success = save_tender_to_db(
                                user_id=current_user_id,
                                project_name=project_name_input,
                                content=content_to_save,
                                section_type=sec_name,
                                category=selected_category,
                                pdf_bytes=pdf_bytes
                            )
                            if success:
                                saved_count += 1
                if saved_count > 0:
                    st.success(f"Ã¢Å“â€¦ {saved_count} sections saved!")
                else:
                    st.warning("Generate sections first.")


# Footer
st.markdown("""
<div style='text-align:center; color:rgba(255,255,255,0.2); font-size:12px; padding:24px 0 16px;
    border-top:1px solid rgba(255,255,255,0.06); margin-top:20px;'>
    <strong style="color:rgba(168,85,247,0.7)">TenderFlow</strong> &middot; Tender Studio &middot; AI-Powered Procurement Intelligence
</div>
""", unsafe_allow_html=True)

