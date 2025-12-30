import streamlit as st
import base64
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
BG_IMAGE = ROOT_DIR / "assets" / "bg.png"

def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

def intro_page():
    bin_str = get_base64(BG_IMAGE)
    bg_css = f'url("data:image/png;base64,{bin_str}")' if bin_str else "none"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Montserrat:wght@800&display=swap');

        /* Hide Streamlit default UI elements */
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        #MainMenu {{visibility: hidden;}}

        .stApp {{
            background:radial-gradient(circle at 20% 30%, #1a1c4b 0%, #0f111a 100%);
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            font-family: 'Inter', sans-serif;
        }}

        /* FIXED: Login Button on the FAR RIGHT corner */
        .login-positioner {{
            position: absolute;
            top: 30px;
            right: 50px;
            z-index: 999999;
        }}

        /* HERO CONTAINER: Centered and Full Width */
        .hero-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            width: 100%;
            margin-top: 12vh;
        }}

        .hero-title {{
            font-family: 'Montserrat', sans-serif !important;
            font-size: 7.5rem !important; 
            font-weight: 800;
            color: #F8F9FA !important;
            margin: 0;
            padding: 0;
            letter-spacing: -4px;
            white-space: nowrap !important; /* Forces title to stay on one line */
            line-height: 1.1;
        }}

        .primary-tagline {{
            color: #a855f7; /* Accent Gold */
            font-size: 1.6rem;
            font-weight: 600;
            margin: 25px 0 10px 0;
        }}

        .description-text {{
            color: #8B949E; /* Secondary Gray */
            font-size: 1.15rem;
            line-height: 1.7;
            max-width: 850px; 
            margin: 0 auto 40px auto;
        }}

        /* ALL BUTTONS: Prevent vertical text (L-o-g-i-n fix) */
        div.stButton > button {{
            background-color: #F8F9FA !important;
            color: #0B1117 !important;
            border: none !important;
            padding: 12px 35px !important;
            border-radius: 6px !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            white-space: nowrap !important; /* Horizontal button text */
            transition: all 0.3s ease !important;
        }}

        div.stButton > button:hover {{
            background-color: #a855f7 !important;
            color: #F8F9FA !important;
            transform: translateY(-2px);
            box-shadow: 0 8px 15px rgba(212, 175, 55, 0.2);
        }}

        .block-container {{
            padding-top: 0rem !important;
            max-width: 100% !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="login-positioner">', unsafe_allow_html=True)
    if st.button("Login", key="btn_login"):
        st.switch_page("pages/loginPage.py")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="hero-container">
            <h1 class="hero-title">TenderFlow</h1>
            <p class="primary-tagline">Built for Speed. Designed for Accuracy.</p>
            <p class="description-text">
                TenderFlow is a centralized platform designed to simplify the entire tender lifecycle — 
                from discovery and documentation to collaboration and submission. Manage tenders 
                efficiently, stay compliant, and meet deadlines with confidence.
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns([1.5, 1, 1.5])
    with c2:
        if st.button("Sign UP", key="btn_signin", use_container_width=True):
            st.switch_page("pages/signPage.py")
    
if __name__ == "__main__" or True:
    intro_page()