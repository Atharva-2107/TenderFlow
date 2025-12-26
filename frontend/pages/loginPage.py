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

        /* IMAGE AND TEXT GAP FIX */
        [data-testid="stImage"] {
            display: flex;
            justify-content: center;
            margin-bottom: 0px !important; 
        }
        
        [data-testid="stImage"] img {
            margin-bottom: -40px !important; 
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
                TenderFlow<br><span style='color: #D4AF37;'>Intelligence.</span>
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

        st.markdown("<p style='text-align:center; color:#2d313e; font-size:10px; margin-top:50px;'>AUTHORISED PERSONNEL ONLY</p>", unsafe_allow_html=True)