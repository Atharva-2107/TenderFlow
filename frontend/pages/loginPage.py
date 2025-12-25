import streamlit as st
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="TenderFlow AI | Login", layout="wide")

def inject_exact_brand_theme():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
        
        .stApp { background-color: #0f111a; font-family: 'Inter', sans-serif; }
        header, footer {visibility: hidden;}
        .block-container {padding: 0 !important;}

        /* Left Side Mesh Gradient */
        .stApp::before {
            content: ""; position: fixed; top: 0; left: 0; width: 50vw; height: 100vh;
            background: radial-gradient(circle at 20% 30%, #1a1c4b 0%, #0f111a 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.05); z-index: 0;
        }

        /* Ghost Input Styling */
        div[data-baseweb="input"] {
            background-color: transparent !important; border: none !important;
            border-bottom: 1.5px solid #2d313e !important; border-radius: 0px !important;
            padding: 10px 0px !important; margin-bottom: 10px;
        }
        div[data-baseweb="input"]:focus-within { border-bottom: 1.5px solid #a855f7 !important; }
        input { color: #ffffff !important; font-size: 16px !important; }

        /* CENTERED BUTTON */
        div.stButton { display: flex; justify-content: center; width: 100%; margin-top: 30px; }
        button[kind="primary"] {
            background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%) !important;
            color: white !important; border-radius: 50px !important;
            padding: 14px 60px !important; font-weight: 700 !important;
            width: auto !important; min-width: 240px; border: none !important;
        }

        /* IMAGE AND TEXT GAP FIX */
        [data-testid="stImage"] {
            display: flex;
            justify-content: center;
            margin-bottom: 0px !important; /* Force zero margin below image */
        }
        
        [data-testid="stImage"] img {
            margin-bottom: -40px !important; /* Pull image container inward */
        }

        [data-testid="stForm"] { border: none !important; padding: 0 !important; }
        </style>
    """, unsafe_allow_html=True)

inject_exact_brand_theme()

col_branding, col_login = st.columns([1.2, 1])

with col_branding:
    st.write("<div style='height: 30vh;'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div style='padding-left: 15%;'>
            <div style='background: #6366f1; width: 45px; height: 5px; border-radius: 10px; margin-bottom: 25px;'></div>
            <h1 style='color: white; font-size: 60px; font-weight: 800; line-height: 1; letter-spacing: -2px; margin: 0;'>
                TenderFlow<br><span style='color: #a855f7;'>Intelligence.</span>
            </h1>
            <p style='color: #94a3b8; font-size: 18px; margin-top: 25px;'>Proprietary AI for procurement.</p>
        </div>
    """, unsafe_allow_html=True)

with col_login:
    st.write("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    _, form_box, _ = st.columns([0.15, 0.7, 0.15])
    
    with form_box:
        current_dir = os.path.dirname(__file__)
        logo_path = os.path.join(current_dir, "..", "assets", "logo.png")
        
        if os.path.exists(logo_path):
            st.image(logo_path, width=280)
        else:
            st.markdown("<h2 style='color:white; text-align:center;'>TenderFlow</h2>", unsafe_allow_html=True)

        # THE GAP KILLER: Negative margin-top pulls this text RIGHT under the logo
        st.markdown("""
            <div style='text-align: center; margin-top: -35px; margin-bottom: 30px;'>
                <p style='color: #6366f1; font-size: 12px; font-weight: 700; letter-spacing: 4px; text-transform: uppercase; line-height: 0;'>
                    Secure Access Portal
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_flow"):
            st.text_input("Work Email", placeholder="Work Email", label_visibility="collapsed")
            st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            st.form_submit_button("Enter Portal", type="primary")

        st.markdown("<p style='text-align:center; color:#2d313e; font-size:10px; margin-top:50px;'>AUTHORISED PERSONNEL ONLY</p>", unsafe_allow_html=True)