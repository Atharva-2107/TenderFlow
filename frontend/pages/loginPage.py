import streamlit as st
<<<<<<< HEAD
from supabase import create_client
import extra_streamlit_components as stx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIG & STYLING ---
st.set_page_config(page_title="TenderFlow AI | Secure Login", layout="wide")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
LLAMA_KEY = os.getenv("LLAMAPARSE_CLOUD_API_KEY")
API_URL = "http://127.0.0.1:8000"

def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("⚠️ Environment variables not found. Check your .env file!")
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

def local_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');
        
        * {
            font-family: 'Poppins', sans-serif;
        }
        
        /* Animated gradient background */
        .stApp {
            background: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #4facfe);
            background-size: 400% 400%;
            animation: gradientShift 15s ease infinite;
        }
        
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        /* Hide Streamlit branding */
        #MainMenu, footer, header {visibility: hidden;}
        .block-container {padding-top: 2rem !important;}
        
        /* Premium login card */
        .login-box {
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(30px);
            border-radius: 28px;
            padding: 50px 45px;
            box-shadow: 
                0 20px 60px rgba(0, 0, 0, 0.3),
                0 0 0 1px rgba(255, 255, 255, 0.1) inset;
            max-width: 440px;
            margin: 60px auto;
            position: relative;
            overflow: hidden;
        }
        
        .login-box::before {
            content: '';
            position:absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 6px;
            background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
            background-size: 500% 500%;
            animation: shimmer 3s linear infinite;
        }
        
        @keyframes shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        
        /* Logo and branding */
        .brand-logo {
            text-align: center;
            margin-bottom: 32px;
        }
        
        .brand-icon {
            width: 70px;
            height: 70px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 18px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 16px;
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
            transition: transform 0.3s ease;
        }
        
        .brand-icon:hover {
            transform: translateY(-4px) scale(1.05);
        }
        
        .brand-title {
            font-size: 34px;
            font-weight: 700;
            background: linear-gradient(135deg, #1e293b 0%, #667eea 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            letter-spacing: -0.5px;
        }
        
        .brand-subtitle {
            color: #1C4D8D;
            font-size: 14px;
            font-weight: 500;
            margin-top: 8px;
        }
        
        /* Input fields */
        .stTextInput label {
            font-size: 13px !important;
            font-weight: 600 !important;
            color: #334155 !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px !important;
        }
        
        .stTextInput input {
            border: 2px solid #e2e8f0 !important;
            border-radius: 14px !important;
            padding: 16px 18px !important;
            font-size: 15px !important;
            background: #f8fafc !important;
            transition: all 0.3s ease !important;
            font-weight: 500;
        }
        
        .stTextInput input:focus {
            border-color: #667eea !important;
            background: white !important;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1) !important;
            transform: translateY(-2px);
        }
        
        .stTextInput input::placeholder {
            color: #94a3b8;
            font-weight: 400;
        }
        
        /* Form spacing */
        [data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
        }
        
        /* Primary button - Sign In */
        button[kind="primary"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 14px !important;
            padding: 16px 24px !important;
            font-size: 16px !important;
            font-weight: 700 !important;
            width: 100% !important;
            margin-top: 24px !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4) !important;
            transition: all 0.3s ease !important;
            cursor: pointer;
        }
        
        button[kind="primary"]:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 15px 35px rgba(102, 126, 234, 0.5) !important;
        }
        
        button[kind="primary"]:active {
            transform: translateY(-1px) !important;
        }
        
        /* Divider */
        hr {
            margin: 32px 0 24px 0 !important;
            border: none !important;
            height: 1px !important;
            background: linear-gradient(90deg, transparent, #e2e8f0, transparent) !important;
        }
        
        /* Secondary buttons */
        .stButton button:not([kind="primary"]) {
            background: white !important;
            color: #475569 !important;
            border: 2px solid #e2e8f0 !important;
            border-radius: 14px !important;
            padding: 14px 20px !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            width: 100% !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton button:not([kind="primary"]):hover {
            background: #f8fafc !important;
            border-color: #cbd5e1 !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important;
        }
        
        /* Floating particles */
        .particle {
            position: fixed;
            width: 3px;
            height: 3px;
            background: rgba(255, 255, 255, 0.6);
            border-radius: 50%;
            pointer-events: none;
            animation: float 20s infinite ease-in-out;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px) translateX(0px); opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { transform: translateY(-100vh) translateX(50px); opacity: 0; }
        }
        
        /* Success/Warning messages */
        .stSuccess, .stWarning, .stError {
            border-radius: 12px !important;
            padding: 12px 16px !important;
            font-weight: 500;
        }
        
        /* Column spacing */
        [data-testid="column"] {
            padding: 0 6px !important;
        }
        </style>
    """, unsafe_allow_html=True)

# Apply CSS
local_css()

# Add floating particles for ambiance
particles_html = ""
for i in range(15):
    top = (i * 7) % 100
    left = (i * 13) % 100
    delay = i * 1.5
    particles_html += f'<div class="particle" style="top: {top}%; left: {left}%; animation-delay: {delay}s;"></div>'

st.markdown(particles_html, unsafe_allow_html=True)

# --- AUTH LOGIC ---
cookie_manager = stx.CookieManager()

def login_user(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.authenticated = True
        st.session_state.user = res.user
        cookie_manager.set("tf_access_token", res.session.access_token, key="login_cookie")
        st.session_state.page = "dashboard"
        st.success("✓ Access Granted - Redirecting...")
        st.rerun()
    except Exception as e:
        st.toast(f"Error: {str(e)}", icon="❌")

# --- UI LAYOUT ---
st.write("")
st.write("")

left_spacer, center_col, right_spacer = st.columns([1, 2, 1])

with center_col:
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    
    # Brand section
    st.markdown("""
        <div class="brand-logo">
            <div class="brand-icon">
                <svg width="38" height="38" viewBox="0 0 64 64" fill="none">
                    <path d="M32 12L44 18V38L32 44L20 38V18L32 12Z" fill="white" opacity="0.9"/>
                    <path d="M28 24H36V32H28V24Z" fill="#667eea"/>
                </svg>
            </div>
            <h1 class="brand-title">TenderFlow AI</h1>
            <p class="brand-subtitle">Secure Intelligence for Procurement Professionals</p>
        </div>
    """, unsafe_allow_html=True)

    # Login form
    with st.form("login_form"):
        email = st.text_input("Email Address", placeholder="your.email@company.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        st.write("")
        
        if st.form_submit_button("Sign In →", type="primary"):
            if email and password:
                login_user(email, password)
            else:
                st.warning("⚠️ Please provide both email and password.")

    st.write("---")
    
    # Navigation buttons
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("Create Account", key="signup", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()
    with nav_col2:
        if st.button("← Back", key="back", use_container_width=True):
            st.session_state.page = "intro"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
=======
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
            background: linear-gradient(rgba(11, 17, 23, 0.85), rgba(11, 17, 23, 0.95));
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
>>>>>>> 8ac450a0ddeef27c9c24e20cac1318507b3dee78
