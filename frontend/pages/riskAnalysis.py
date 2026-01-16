import streamlit as st
import plotly.graph_objects as go
import random
import sys
from pathlib import Path

# --------------------------------------------------
# FIX 1: Ensure project root is in sys.path FIRST
# --------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Correct import because utils is inside frontend
from frontend.utils.auth import can_access
from backend.risk_engine import analyze_pdf

# --------------------------------------------------
# ACCESS CONTROL
# --------------------------------------------------
if not can_access("risk_analysis"):
    st.error("You are not authorized to access this page.")
    st.stop()

# --------------------------------------------------
# SESSION STATE INITIALIZATION
# --------------------------------------------------
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

if "last_file_id" not in st.session_state:
    st.session_state.last_file_id = None

# --------------------------------------------------
# MAIN PAGE
# --------------------------------------------------
def risk_analysis_page():

    # ------------------ STYLING ------------------
    st.markdown("""
        <style>
        .stApp {
            background: radial-gradient(circle at 20% 30%, #1a1c4b 0%, #0f111a 100%) !important;
        }
        [data-testid="stAppViewContainer"] {
            background: transparent !important;
        }
        [data-testid="stHeader"] {
            background: rgba(2, 6, 23, 0.85) !important;
        }

        .risk-header { font-size: 2.2rem; font-weight: 700; color: #94a3b8; }
        .risk-tag {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 8px;
        }
        .tag-financial { background-color: #fee2e2; color: #991b1b; }
        .tag-legal { background-color: #e0f2fe; color: #075985; }
        .tag-resource { background-color: #fef3c7; color: #92400e; }
        .tag-payment { background-color: #f3e8ff; color: #6b21a8; }
        .tag-timeline { background-color: #f3e8ff; color: #6b21a8; }

        .risk-card {
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.2rem;
            border: 1px solid #1f2937;
            background-color: #0f172a;
            box-shadow: 0 6px 18px rgba(0,0,0,0.35);
        }

        .border-red { border-left: 6px solid #ef4444; }
        .border-amber { border-left: 6px solid #f59e0b; }
        .border-green { border-left: 6px solid #22c55e; }
        </style>
    """, unsafe_allow_html=True)

    # ------------------ HEADER ------------------
    st.markdown('<div class="risk-header">🕵️ Contractual Risk Intelligence</div>', unsafe_allow_html=True)
    st.write("AI-driven deep scan of Tender Documents for contractual and financial risk.")

    # ------------------ FILE UPLOAD ------------------
    uploaded_file = st.file_uploader(
        "Upload Tender RFP or Contract Draft",
        type=["pdf"],
        key="risk_pdf_uploader"
    )

    # ------------------ ANALYSIS TRIGGER ------------------
    if uploaded_file:
        file_id = (uploaded_file.name, uploaded_file.size)

        if st.session_state.last_file_id != file_id:
            with st.status("AI Risk Engine Analyzing Document...", expanded=True) as status:
                st.write("Extracting clauses from document...")
                st.write("Running legal risk classification model...")
                st.session_state.analysis_results = analyze_pdf(uploaded_file)
                st.session_state.last_file_id = file_id
                status.update(label="Analysis Complete", state="complete")

    st.divider()

    # ------------------ SIDEBAR CONTROLS ------------------
    if st.session_state.analysis_results:
        with st.sidebar:
            st.header("⚙️ View Settings")

            appetite = st.slider(
                "Risk Sensitivity Threshold",
                0, 100, 20,
                help="Hide risks below this severity score."
            )

            focus_cats = st.multiselect(
                "Filter by Category",
                ['Financial', 'Timeline', 'Legal', 'Payment', 'Resource'],
                default=['Financial', 'Timeline', 'Legal', 'Payment', 'Resource']
            )

            if st.button("Clear Analysis"):
                st.session_state.analysis_results = None
                st.session_state.last_file_id = None
                st.rerun()

    # ------------------ RESULTS ------------------
    if st.session_state.analysis_results:
        filtered_data = [
            r for r in st.session_state.analysis_results
            if r["severity"] >= appetite and r["category"] in focus_cats
        ]

        col_chart, col_summary = st.columns(2)

        # ---------- Radar Chart ----------
        with col_chart:
            cats = ['Financial', 'Timeline', 'Legal', 'Payment', 'Resource']
            vals = []

            for c in cats:
                scores = [r["severity"] for r in st.session_state.analysis_results if r["category"] == c]
                vals.append(sum(scores) / len(scores) if scores else 0)

            fig = go.Figure(go.Scatterpolar(
                r=vals,
                theta=cats,
                fill="toself",
                line_color="#ef4444"
            ))

            fig.update_layout(
                polar=dict(radialaxis=dict(range=[0, 100], visible=True)),
                showlegend=False,
                height=350
            )

            st.plotly_chart(fig, use_container_width=True)

        # ---------- Summary ----------
        with col_summary:
            critical = [r for r in filtered_data if r["status"] == "Critical"]
            warning = [r for r in filtered_data if r["status"] == "Warning"]

            st.metric("Critical Risks", len(critical), delta=f"{len(warning)} Warnings")

            if critical:
                top = max(critical, key=lambda x: x["severity"])
                st.error(f"Highest Risk: {top['clause']} ({top['severity']}/100)")
            else:
                st.success("No critical risks under current filters.")

        st.divider()

        # ---------- Clause Cards ----------
        st.subheader(f"🔍 Clause Breakdown ({len(filtered_data)} flags)")

        if not filtered_data:
            st.info("No clauses match your filters.")
        else:
            for r in filtered_data:
                border = (
                    "border-red" if r["status"] == "Critical"
                    else "border-amber" if r["status"] == "Warning"
                    else "border-green"
                )

                st.markdown(f"""
                    <div class="risk-card {border}">
                        <span class="risk-tag {r['tag_class']}">{r['category']}</span>
                         <h4>{r['clause']} </h4>
                        <p style="font-style: italic;">"{r['content']}"</p>
                        <p><strong>AI Analysis:</strong> {r['impact']}</p>
                    </div>
                """, unsafe_allow_html=True)

    else:
        st.info("Upload a contract or tender document to begin analysis.")


if __name__ == "__main__":
    risk_analysis_page()
