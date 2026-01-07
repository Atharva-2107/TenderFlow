import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TenderFlow | Enterprise RAG Platform",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; font-family: 'Inter', sans-serif; }
    
    .top-bar {
        background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
        padding: 1.2rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Role Selection Card Styling */
    .role-card {
        background-color: white;
        padding: 30px;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        text-align: center;
        transition: transform 0.2s;
        cursor: pointer;
    }
    .role-card:hover {
        transform: translateY(-5px);
        border-color: #3b82f6;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    .step-item {
        flex: 1;
        text-align: center;
        padding: 10px;
        border-bottom: 4px solid #e2e8f0;
        color: #94a3b8;
        font-weight: 600;
    }
    .step-active { border-bottom: 4px solid #3b82f6; color: #1e293b; }
    .step-complete { border-bottom: 4px solid #10b981; color: #10b981; }

    .guide-box {
        background-color: #f0f7ff; 
        padding: 20px; 
        border-left: 5px solid #3b82f6; 
        border-radius: 8px; 
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. SESSION STATE
# -----------------------------------------------------------------------------
if 'user_role' not in st.session_state:
    st.session_state.user_role = None  # Start with no role selected

if 'step_index' not in st.session_state:
    st.session_state.step_index = 0

def set_role(role):
    st.session_state.user_role = role
    st.session_state.step_index = 0

def next_step():
    st.session_state.step_index += 1

def prev_step():
    st.session_state.step_index -= 1

# -----------------------------------------------------------------------------
# 3. LANDING PAGE: ROLE SELECTION
# -----------------------------------------------------------------------------
if st.session_state.user_role is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>Welcome to TenderFlow AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b;'>Select your workspace to begin</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b, col_c, col_d = st.columns([1, 2, 2, 1])
    
    with col_b:
        st.markdown('<div class="role-card">', unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
        st.markdown("### I am an Issuer")
        st.caption("I want to create a tender and find the best contractors.")
        if st.button("Enter Client Workspace", key="btn_issuer", use_container_width=True):
            set_role("Issuer")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_c:
        st.markdown('<div class="role-card">', unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/3281/3281289.png", width=80)
        st.markdown("### I am a Bidder")
        st.caption("I want to analyze tenders and submit winning bids.")
        if st.button("Enter Contractor Workspace", key="btn_bidder", use_container_width=True):
            set_role("Bidder")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. WORKSPACE: ISSUER OR BIDDER
# -----------------------------------------------------------------------------
else:
    # Sidebar remains for secondary info
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2910/2910795.png", width=40)
        st.markdown("### TenderFlow Pro")
        st.markdown("---")
        st.write(f"**Mode:** {st.session_state.user_role}")
        if st.button("🔄 Switch Role / Exit"):
            st.session_state.user_role = None
            st.rerun()

    # Define Workflow Steps
    issuer_steps = ["1. Project Details", "2. Technical Scope", "3. Financials (BOQ)", "4. Publish"]
    bidder_steps = ["1. Upload Tender", "2. AI Summary", "3. Gap Analysis", "4. Submit Bid"]
    current_steps = issuer_steps if st.session_state.user_role == "Issuer" else bidder_steps

    # Progress Tracker
    step_cols = st.columns(len(current_steps))
    for i, s_label in enumerate(current_steps):
        is_active = "step-active" if i == st.session_state.step_index else ""
        is_complete = "step-complete" if i < st.session_state.step_index else ""
        step_cols[i].markdown(f"""<div class="step-item {is_active} {is_complete}">{s_label}</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Header Bar
    bar_color = "#3b82f6" if st.session_state.user_role == "Issuer" else "#10b981"
    st.markdown(f"""
        <div class="top-bar" style="background: {bar_color};">
            <h1>{current_steps[st.session_state.step_index]}</h1>
            <div style="font-weight: 500;">Role: {st.session_state.user_role}</div>
        </div>
    """, unsafe_allow_html=True)

    # --- ISSUER LOGIC ---
    if st.session_state.user_role == "Issuer":
        if st.session_state.step_index == 0:
            st.subheader("General Information")
            st.text_input("Project Name", placeholder="e.g. Mumbai Metro Phase II")
            st.date_input("Submission Deadline")

        elif st.session_state.step_index == 1:
            st.markdown("""
                <div class="guide-box">
                    <h4 style="margin-top:0; color: #1e3a8a;">📝 How to describe your requirements</h4>
                    <ul style="font-size: 0.9rem; color: #1e40af; line-height: 1.6;">
                        <li><b>🏗️ Physical Scale:</b> Dimensions, floors, or volume of work.</li>
                        <li><b>📍 Exact Location:</b> City and site conditions.</li>
                        <li><b>💎 Target Quality:</b> Define standards (e.g., "IS Code 456").</li>
                        <li><b>💰 Budget & Timeline:</b> Project value and deadline.</li>
                        <li><b>🛠️ Tech & Materials:</b> Must-haves like "M40 Concrete".</li>
                        <li><b>📜 Bidder Profile:</b> Min. experience required.</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
            st.text_area("Detailed Project Description", height=200, placeholder="Enter details based on the guide above...")

        elif st.session_state.step_index == 2:
            st.subheader("Financial Component Builder")
            df = pd.DataFrame([{"Item": "Civil Works", "Qty": 1, "Rate": 10000}])
            st.data_editor(df, num_rows="dynamic", use_container_width=True)

        elif st.session_state.step_index == 3:
            st.success("Tender Ready!")
            st.button("Download Professional PDF")

    # --- BIDDER LOGIC ---
    else:
        if st.session_state.step_index == 0:
            st.subheader("Upload Client Tender")
            st.file_uploader("Upload PDF")
        elif st.session_state.step_index == 1:
            st.info("AI Analysis will be displayed here.")
        # ... and so on

    # --- FOOTER NAVIGATION ---
    st.markdown("---")
    f_col1, f_col2, f_col3 = st.columns([1, 4, 1])
    with f_col1:
        if st.session_state.step_index > 0:
            st.button("⬅️ Back", on_click=prev_step, use_container_width=True)
    with f_col3:
        if st.session_state.step_index < len(current_steps) - 1:
            st.button("Save & Next ➡️", on_click=next_step, type="primary", use_container_width=True)
        else:
            if st.button("Finish 🚀", type="primary", use_container_width=True):
                st.balloons()


