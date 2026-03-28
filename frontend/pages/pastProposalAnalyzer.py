import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import plotly.express as px
import requests
import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# ── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TenderFlow | Past Proposal Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase credentials not found.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    from utils.auth import can_access
except ImportError:
    def can_access(feature): return True

def get_base64_of_bin_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def format_inr(number):
    try:
        number = float(number)
        if number == 0:
            return "—"
        if number < 0:
            return "-" + format_inr(-number)
        
        if number >= 10_000_000:
            return f"₹{number/10_000_000:.2f} Cr"
        elif number >= 100_000:
            return f"₹{number/100_000:.2f} L"
        else:
            return f"₹{number:,.0f}"
    except Exception:
        return f"₹{number}"

# ── Auth Guard ───────────────────────────────────────────────────────────────
if not st.session_state.get("authenticated"):
    st.error("Please login to continue.")
    st.stop()
if not st.session_state.get("active_company_id"):
    st.error("Company context missing. Please login again.")
    st.stop()

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp {
    background: radial-gradient(ellipse 120% 80% at 18% 25%, #1e1b4b 0%, #0c0a1d 55%, #030014 100%) !important;
}
header, footer { visibility: hidden; }
div.block-container {
    padding-top: 0.4rem !important;
    padding-bottom: 2rem !important;
}
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(168,85,247,0.35); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(168,85,247,0.6); }

.label-text {
    color: rgba(168,85,247,0.65) !important;
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.stButton>button {
    width: 100%;
    border-radius: 14px !important;
    border: none !important;
    background: linear-gradient(135deg, #7c3aed 0%, #a855f7 50%, #c084fc 100%) !important;
    color: white !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    padding: 0.65rem 1rem !important;
    box-shadow: 0 4px 18px rgba(124,58,237,0.25) !important;
    transition: all 0.25s cubic-bezier(.4,0,.2,1) !important;
}
.stButton>button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 28px rgba(124,58,237,0.38) !important;
}
.stButton>button:disabled { opacity: 0.45 !important; }

[data-testid="stFileUploadDropzone"] {
    background: rgba(168,85,247,0.04) !important;
    border: 2px dashed rgba(168,85,247,0.30) !important;
    border-radius: 16px !important;
    transition: all 0.2s ease !important;
}
[data-testid="stFileUploadDropzone"]:hover {
    background: rgba(168,85,247,0.08) !important;
    border-color: rgba(168,85,247,0.50) !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: rgba(255,255,255,0.07) !important;
    border-radius: 18px !important;
    background: rgba(255,255,255,0.015) !important;
}

hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, rgba(168,85,247,0.30), transparent) !important;
    margin: 12px 0 18px 0 !important;
}

.stat-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(168,85,247,0.18);
    border-radius: 18px;
    padding: 20px 16px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #7c3aed, #a855f7, #c084fc);
}
.stat-label {
    color: rgba(168,85,247,0.55);
    font-size: 9px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 8px;
}
.stat-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.5rem;
    font-weight: 700;
    color: #c084fc;
}
.stat-sub {
    color: rgba(255,255,255,0.30);
    font-size: 10px;
    margin-top: 4px;
}
.insight-item {
    padding: 8px 14px;
    margin-bottom: 7px;
    border-radius: 10px;
    background: rgba(255,255,255,0.03);
    font-size: 12.5px;
    color: rgba(255,255,255,0.72);
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
left, center = st.columns([3, 6])
with left:
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
    logo = get_base64_of_bin_file(logo_path)
    if logo:
        st.markdown(f'<img src="data:image/png;base64,{logo}" width="180" style="margin-top:4px">', unsafe_allow_html=True)

with center:
    header_cols = st.columns([3, 0.5, 0.5, 0.5, 0.5, 0.5])
    with header_cols[1]:
        if st.button("⊞", key="h_dash", help="Dashboard"):
            st.switch_page("app.py")
    with header_cols[2]:
        if can_access("tender_generation"):
            if st.button("⎘", key="h_gen", help="Tender Generation"):
                st.switch_page("pages/tenderGeneration.py")
        else:
            st.button("⎘", key="h_gen_disabled", disabled=True)
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

# ── Page Title ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="
    display:flex;justify-content:space-between;align-items:center;
    margin:8px 0 22px;padding:22px 28px;
    background:linear-gradient(135deg, rgba(124,58,237,0.12) 0%, rgba(15,17,26,0.85) 40%, rgba(168,85,247,0.08) 100%);
    border:1px solid rgba(168,85,247,0.18);border-radius:22px;
    backdrop-filter:blur(10px);position:relative;overflow:hidden;
">
    <div style="position:absolute;top:-40%;right:-5%;width:280px;height:280px;
         background:radial-gradient(circle,rgba(168,85,247,0.14) 0%,transparent 70%);pointer-events:none;"></div>
    <div style="position:relative;z-index:1;">
        <div style="font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:2.5px;color:rgba(168,85,247,0.65);margin-bottom:6px;">AI-Powered Module</div>
        <h1 style="font-size:2rem;font-weight:900;background:linear-gradient(135deg,#fff 0%,#e9d5ff 40%,#c084fc 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;letter-spacing:-0.5px;">Past Proposal Analyzer</h1>
        <p style="color:rgba(255,255,255,0.40);font-size:12.5px;margin:4px 0 0;font-weight:500;">Analyze past tender PDFs to discover winning bid patterns, qualification insights & competitive intelligence</p>
    </div>
    <div style="padding:8px 18px;border:1px solid rgba(168,85,247,0.30);border-radius:100px;background:rgba(168,85,247,0.10);color:#c084fc;font-size:10px;font-weight:800;letter-spacing:1px;text-transform:uppercase;">Competitive Intel</div>
</div>
""", unsafe_allow_html=True)

# ── Fetch Bid History Stats from DB ─────────────────────────────────────────
hist_avg_bid = 0.0
hist_win_rate = 0.0
hist_count = 0
hist_total_value = 0.0
try:
    company_id = st.session_state.get("active_company_id")
    if company_id:
        hist_res = supabase.table("bid_history_v2").select("final_bid_amount, won").eq("company_id", company_id).execute()
        if hist_res.data:
            hist_count = len(hist_res.data)
            bids_lakh = [r["final_bid_amount"] for r in hist_res.data if r.get("final_bid_amount")]
            if bids_lakh:
                hist_avg_bid = (sum(bids_lakh) / len(bids_lakh)) * 100_000
                hist_total_value = sum(bids_lakh) * 100_000
            wins = [r for r in hist_res.data if r.get("won") is True]
            hist_win_rate = (len(wins) / hist_count * 100) if hist_count > 0 else 0
except Exception:
    pass

# ── DB Stats Mini-Banner ─────────────────────────────────────────────────────
if hist_count > 0:
    db_c1, db_c2, db_c3, db_c4 = st.columns(4)
    def db_stat(col, label, value, color="#c084fc"):
        with col:
            st.markdown(f"""
            <div class="stat-card" style="padding:14px 12px;">
                <div class="stat-label">{label}</div>
                <div class="stat-value" style="font-size:1.2rem;color:{color};">{value}</div>
            </div>""", unsafe_allow_html=True)
    db_stat(db_c1, "📋 Saved Bids", str(hist_count))
    db_stat(db_c2, "💰 Avg Bid Saved", format_inr(hist_avg_bid), "#e9d5ff")
    db_stat(db_c3, "🏆 Win Rate", f"{hist_win_rate:.1f}%", "#4ade80")
    db_stat(db_c4, "📊 Total Bid Value", format_inr(hist_total_value), "#fbbf24")
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Main Content: Upload | Analysis ─────────────────────────────────────────
if "ppa_analysis" not in st.session_state:
    st.session_state.ppa_analysis = None

upload_col, result_col = st.columns([1.2, 1.8], gap="large")

with upload_col:
    st.markdown('<p class="label-text">📁 Upload Tender Documents</p>', unsafe_allow_html=True)
    st.caption("Upload 1–10 past tender PDFs. The AI will extract budgets, qualification patterns & winning strategies.")

    with st.container(border=True):
        past_files = st.file_uploader(
            "Upload past tender PDFs",
            type=["pdf"],
            accept_multiple_files=True,
            key="ppa_uploader",
            label_visibility="collapsed"
        )
        include_samples = st.checkbox("Also include 5 built-in Sample Tenders in analysis", value=False)

    # ── Action Buttons ──
    btn_c1, btn_c2 = st.columns(2)
    with btn_c1:
        analyze_clicked = st.button("🔍 Analyze Uploaded", use_container_width=True, key="btn_ppa_analyze",
                                     disabled=(not past_files and not include_samples))
    with btn_c2:
        sample_clicked = st.button("🧪 Use Sample Tenders", use_container_width=True, key="btn_ppa_samples")

    # ── Sample Tenders Info ──
    st.markdown("""
    <div style="margin-top:14px;padding:14px 16px;border-radius:14px;
         background:rgba(168,85,247,0.06);border:1px solid rgba(168,85,247,0.15);">
        <div style="font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:1.5px;
             color:rgba(168,85,247,0.65);margin-bottom:8px;">📦 Built-in Sample Tenders</div>
        <div style="font-size:11.5px;color:rgba(255,255,255,0.55);line-height:1.7;">
            Click <b style="color:#c084fc;">Use Sample Tenders</b> to analyze 5 real Indian government tender templates:<br>
            • CPWD Highway Construction<br>
            • NHAI Road Development 2025<br>
            • PWD Bridge Renovation<br>
            • Municipal Water Supply<br>
            • Railway Station Modernization
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Error / Info ──
    if analyze_clicked and past_files:
        with st.spinner("🧠 AI is analyzing your tenders..."):
            try:
                api_files = [("files", (f.name, f.getvalue(), "application/pdf")) for f in past_files]
                data = {"include_samples": "true" if include_samples else "false"}
                resp = requests.post("https://tenderflow-iwpl.onrender.com/analyze-past-tenders", files=api_files, data=data, timeout=120)
                if resp.status_code == 200:
                    st.session_state.ppa_analysis = resp.json()
                    st.toast(f"✅ Analyzed {st.session_state.ppa_analysis['tender_count']} tenders!")
                    st.rerun()
                else:
                    st.error(f"API Error {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                st.error(f"Analysis failed: {e}")

    elif analyze_clicked and not past_files and not include_samples:
        st.warning("⚠️ Upload at least one PDF or check the sample tenders box.")

    if sample_clicked:
        with st.spinner("🧪 Loading & analyzing sample tenders..."):
            try:
                resp = requests.get("http://localhost:8000/analyze-sample-tenders", timeout=90)
                if resp.status_code == 200:
                    st.session_state.ppa_analysis = resp.json()
                    st.toast(f"✅ Analyzed {st.session_state.ppa_analysis['tender_count']} sample tenders!")
                    st.rerun()
                else:
                    st.error(f"API Error {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                st.error(f"Sample analysis failed: {e}")

# ── Right Panel: Results ─────────────────────────────────────────────────────
with result_col:
    analysis = st.session_state.ppa_analysis

    if analysis:
        agg = analysis.get("aggregate", {})
        avg_budget = agg.get("avg_budget", 0)
        min_budget = agg.get("min_budget", 0)
        max_budget = agg.get("max_budget", 0)
        total_budget = agg.get("total_budget", 0)
        tender_count = analysis.get("tender_count", 0)

        # ── 4 Stat Cards ──
        c1, c2, c3, c4 = st.columns(4)
        def stat(col, label, val, color="#c084fc", sub=""):
            with col:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">{label}</div>
                    <div class="stat-value" style="color:{color};font-size:1.1rem;">{val}</div>
                    <div class="stat-sub">{sub}</div>
                </div>""", unsafe_allow_html=True)

        stat(c1, "Avg Budget", format_inr(avg_budget), "#c084fc", f"{tender_count} tenders")
        stat(c2, "Lowest Bid", format_inr(min_budget), "#4ade80", "min across tenders")
        stat(c3, "Highest Bid", format_inr(max_budget), "#f87171", "max across tenders")
        stat(c4, "Total Value", format_inr(total_budget), "#fbbf24", "combined")

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        # ── Budget Bar Chart ──
        tenders_list = analysis.get("tenders", [])
        budgets_valid = [t for t in tenders_list if t.get("budget", 0) > 0]
        if budgets_valid:
            st.markdown('<p class="label-text">📊 Tender Budget Breakdown</p>', unsafe_allow_html=True)
            names = [t["filename"].replace(".pdf", "").replace("_", " ")[:28] for t in budgets_valid]
            vals = [t["budget"] for t in budgets_valid]
            colors = ["#7c3aed", "#a855f7", "#c084fc", "#9333ea", "#6d28d9"]

            fig = go.Figure(go.Bar(
                x=names,
                y=vals,
                marker_color=[colors[i % len(colors)] for i in range(len(names))],
                text=[format_inr(v) for v in vals],
                textposition="outside",
                textfont=dict(color="rgba(255,255,255,0.7)", size=10, family="JetBrains Mono"),
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="rgba(255,255,255,0.6)", family="Inter", size=10),
                height=220,
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis=dict(showgrid=False, tickfont=dict(size=9)),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickformat=",.0f"),
                bargap=0.3,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # ── Qualification Patterns & Winning Insights ──
        qi_c1, qi_c2 = st.columns(2, gap="medium")

        with qi_c1:
            st.markdown('<p class="label-text">🎯 Qualification Patterns</p>', unsafe_allow_html=True)
            for q in analysis.get("qualification_patterns", [])[:6]:
                st.markdown(f'<div class="insight-item" style="border-left:3px solid rgba(168,85,247,0.45);">{q}</div>', unsafe_allow_html=True)

        with qi_c2:
            st.markdown('<p class="label-text">💡 Winning Strategies</p>', unsafe_allow_html=True)
            for w in analysis.get("winning_insights", [])[:5]:
                st.markdown(f'<div class="insight-item" style="border-left:3px solid rgba(74,222,128,0.45);">{w}</div>', unsafe_allow_html=True)

        # ── BOQ Categories ──
        boq_cats = analysis.get("boq_categories", [])
        if boq_cats:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown('<p class="label-text">📋 Common BOQ Categories</p>', unsafe_allow_html=True)
            boq_cols = st.columns(min(len(boq_cats), 3))
            for i, cat in enumerate(boq_cats[:6]):
                with boq_cols[i % 3]:
                    st.markdown(f"""
                    <div style="padding:8px 12px;border-radius:10px;background:rgba(255,255,255,0.03);
                         border:1px solid rgba(168,85,247,0.14);margin-bottom:6px;
                         font-size:11.5px;color:rgba(255,255,255,0.65);">
                        📦 {cat}
                    </div>""", unsafe_allow_html=True)

        # ── Per Tender Table ──
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.markdown('<p class="label-text">📂 Per-Tender Details</p>', unsafe_allow_html=True)
        max_b = max([t.get("budget", 0) for t in tenders_list], default=1)
        for t in tenders_list:
            b = t.get("budget", 0)
            emd = t.get("emd", 0)
            name = t.get("filename", "Unknown").replace(".pdf", "").replace("_", " ")
            bar_pct = min(100, (b / max(max_b, 1)) * 100) if b > 0 else 0
            err = t.get("error", "")
            status_color = "#f87171" if err else ("#4ade80" if b > 0 else "#f59e0b")
            status_text = "Error" if err else ("Extracted" if b > 0 else "Not Found")
            st.markdown(f"""
            <div style="margin-bottom:10px;padding:12px 16px;border-radius:14px;
                 background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.06);">
                <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                    <span style="color:rgba(255,255,255,0.70);font-size:12px;font-weight:600;">{name}</span>
                    <span style="color:{status_color};font-size:10px;font-weight:700;background:rgba(0,0,0,0.3);
                         padding:2px 8px;border-radius:20px;">{status_text}</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                    <span style="color:#c084fc;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:700;">
                        Budget: {format_inr(b) if b > 0 else '—'}
                    </span>
                    <span style="color:rgba(255,255,255,0.40);font-size:11px;">
                        EMD: {format_inr(emd) if emd > 0 else '—'}
                    </span>
                </div>
                <div style="width:100%;height:5px;background:rgba(255,255,255,0.06);border-radius:10px;overflow:hidden;">
                    <div style="width:{bar_pct:.0f}%;height:100%;background:linear-gradient(90deg,#7c3aed,#a855f7);border-radius:10px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    else:
        # ── Empty State ──
        st.markdown("""
        <div style="text-align:center;padding:60px 28px;border:1px dashed rgba(168,85,247,0.20);
             border-radius:22px;background:rgba(255,255,255,0.012);">
            <div style="font-size:52px;margin-bottom:16px;filter:drop-shadow(0 4px 12px rgba(168,85,247,0.3));">🔮</div>
            <div style="font-size:1.2rem;font-weight:800;background:linear-gradient(135deg,#fff,#e9d5ff);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px;">
                No Analysis Yet
            </div>
            <div style="color:rgba(255,255,255,0.45);font-size:13px;line-height:1.7;max-width:380px;margin:0 auto;">
                Upload past tender PDFs and click <b style="color:#c084fc;">Analyze Uploaded</b><br>
                — or click <b style="color:#c084fc;">Use Sample Tenders</b> to instantly see a demo<br>
                with 5 real Indian government tender templates.
            </div>
            <div style="margin-top:20px;display:flex;justify-content:center;gap:16px;flex-wrap:wrap;">
                <div style="padding:8px 16px;border-radius:12px;background:rgba(168,85,247,0.10);
                     border:1px solid rgba(168,85,247,0.22);color:#c084fc;font-size:11px;font-weight:700;">
                    📊 Avg Winning Bid
                </div>
                <div style="padding:8px 16px;border-radius:12px;background:rgba(74,222,128,0.08);
                     border:1px solid rgba(74,222,128,0.20);color:#4ade80;font-size:11px;font-weight:700;">
                    🎯 Qualification Patterns
                </div>
                <div style="padding:8px 16px;border-radius:12px;background:rgba(251,191,36,0.08);
                     border:1px solid rgba(251,191,36,0.20);color:#fbbf24;font-size:11px;font-weight:700;">
                    💡 Winning Strategies
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
