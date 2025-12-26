import streamlit as st
import os
import base64

# --- PAGE CONFIG ---
st.set_page_config(page_title="TenderFlow AI | Login", layout="wide")

def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def inject_exact_brand_theme():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

        .stApp {
            background-color: #0f111a;
            font-family: 'Inter', sans-serif;
        }

        header, footer { visibility: hidden; }
        .block-container { padding: 0 !important; }

        /* Left panel */
        .stApp::before {
            content: ""; position: fixed; top: 0; left: 0; width: 50vw; height: 100vh;
            background: radial-gradient(circle at 20% 30%, #1a1c4b 0%, #0f111a 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.05); z-index: 0;
        }

        /* --- UPDATED INPUT STYLING --- */
        div[data-baseweb="input"] {
            background-color: rgba(255, 255, 255, 0.03) !important; 
            border: 1px solid #2d313e !important; 
            border-radius: 8px !important;
            padding: 8px 12px !important; 
            transition: all 0.3s ease-in-out !important;
        }
        
        /* Focus state with glow */
        div[data-baseweb="input"]:focus-within { 
            border: 1px solid #a855f7 !important; 
            box-shadow: 0 0 15px rgba(168, 85, 247, 0.2) !important;
            background-color: rgba(168, 85, 247, 0.05) !important;
        }
        
        input { 
            color: #ffffff !important; 
            font-size: 15px !important; 
            font-weight: 400 !important;
        }
        
        /* Placeholder styling */
        input::placeholder {
            color: #4b5563 !important;
            opacity: 1;
        }

        /* CENTERED BUTTON */
        div.stButton { display: flex; justify-content: center; width: 100%; margin-top: 30px; }
        button[kind="primary"] {
            background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%) !important;
            color: white !important; border-radius: 50px !important;
            padding: 14px 60px !important; font-weight: 700 !important;
            width: auto !important; min-width: 240px; border: none !important;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
        }
        button[kind="primary"]:hover {
            box-shadow: 0 6px 20px rgba(168, 85, 247, 0.4);
            transform: translateY(-1px);
        }

        div[data-baseweb="input"]:focus-within {
            border-bottom: 2px solid #6366f1 !important;
        }

        input {
            color: #ffffff !important;
            font-size: 20px !important;
            font-weight: 500 !important;
        }

        /* Kill helper text */
        div[data-baseweb="input"] ~ div,
        div[data-baseweb="input"] div[role="alert"],
        div[data-baseweb="input"] div[aria-live],
        div[data-baseweb="input"] + div,
        [data-testid="stFormInstructions"],
        [data-testid="stFormInstructions"] * {
            display: none !important;
        }

        /* Labels */
        div[data-testid="stWidgetLabel"] p {
            font-size: 14px !important;
            color: #94a3b8 !important;
            margin-bottom: 10px !important;
        }

        /* Button */
        div.stButton {
            display: flex;
            justify-content: center;
            margin-bottom: 0px !important; 
        }
        
        [data-testid="stImage"] img {
            margin-bottom: -40px !important; 
        }

        button[kind="primary"] {
            background: linear-gradient(90deg, #6366f1, #a855f7) !important;
            color: white !important;
            border-radius: 50px !important;
            padding: 18px 60px !important;
            font-size: 18px !important;
            font-weight: 700 !important;
            border: none !important;
            min-width: 280px;
        }

        [data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

inject_exact_brand_theme()

# --- MAIN LAYOUT ---
col_branding, col_login = st.columns([1.2, 1])

# LEFT BRANDING
with col_branding:
    st.markdown("<div style='height:30vh'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div style='padding-left:15%'>
            <div style='background:#6366f1;width:45px;height:5px;border-radius:10px;margin-bottom:25px'></div>
            <h1 style='color:white;font-size:60px;font-weight:800;line-height:1'>
                TenderFlow<br>
                <span style='color:#D4AF37'>Intelligence.</span>
            </h1>
            <p style='color:#94a3b8;font-size:18px;margin-top:25px'>
                Proprietary AI for procurement.
            </p>
        </div>
    """, unsafe_allow_html=True)

# RIGHT LOGIN (STREAMLIT-SAFE CENTERING)
with col_login:
    # top spacer
    st.markdown("<div style='height:18vh'></div>", unsafe_allow_html=True)

    _, box, _ = st.columns([0.2, 0.6, 0.2])

    with box:
        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")
        logo_base64 = get_base64_of_bin_file(logo_path)

        if logo_base64:
            st.markdown(
                f"""
                <div style="text-align:center; margin-bottom: 14px;">
                    <img src="data:image/png;base64,{logo_base64}" width="280">
                </div>
                <div style="text-align:center; margin-bottom: 35px;">
                    <p style="
                        color:#6366f1;
                        font-size:12px;
                        letter-spacing:4px;
                        font-weight:700;
                        margin:0;
                    ">
                        SECURE ACCESS PORTAL
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("""
            <div style='text-align: center; margin-top: -35px; margin-bottom: 30px;'>
                <p style='color: #6366f1; font-size: 12px; font-weight: 700; letter-spacing: 4px; text-transform: uppercase; line-height: 0;'>
                    Secure Access Portal
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_flow"):
            # These will now follow the new "Glass/Box" style defined in CSS
            st.text_input("Work Email", placeholder="Work Email", label_visibility="collapsed")
            st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            st.form_submit_button("Enter Portal", type="primary")

        st.markdown(
            "<p style='text-align:center;color:#2d313e;font-size:10px;margin-top:50px'>AUTHORISED PERSONNEL ONLY</p>",
            unsafe_allow_html=True
        )
