import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(page_title="TenderFlow AI", layout="wide")

def inject_custom_styling():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        /* 1. Reset Global Styles */
        .stApp {
            background-color: #000000;
            font-family: 'Inter', sans-serif;
        }
        
        header, footer {visibility: hidden;}
        .block-container {padding: 0 !important;}

        /* 2. Left Side Mesh Gradient (Matching your high-end image) */
        .stApp::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 50vw;
            height: 100vh;
            background: radial-gradient(circle at 20% 30%, #1a1c4b 0%, #000000 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
            z-index: 0;
        }

        /* 3. INPUT FIELD STYLING (No grey box, clean dark look) */
        div[data-baseweb="input"] {
            background-color: #0a0a0a !important;
            border: 1px solid #1f2937 !important;
            border-radius: 8px !important;
            padding: 8px !important;
            transition: 0.3s all ease;
        }
        
        div[data-baseweb="input"]:focus-within {
            border-color: #6366f1 !important;
            box-shadow: 0 0 10px rgba(99, 102, 241, 0.2) !important;
        }

        /* 4. THE CENTERED "ENTER PORTAL" BUTTON (Separate Styling) */
        /* This container fix forces the button to the center */
        div.stButton {
            display: flex;
            justify-content: center;
            width: 100%;
            margin-top: 30px;
        }

        button[kind="primary"] {
            background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
            color: white !important;
            border-radius: 10px !important;
            padding: 12px 60px !important; /* Wide, premium feel */
            font-weight: 700 !important;
            font-size: 15px !important;
            border: none !important;
            width: auto !important; /* Prevents stretching to full width */
            min-width: 220px;
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3) !important;
            transition: 0.4s all cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        }
        
        button[kind="primary"]:hover {
            transform: scale(1.05) translateY(-2px);
            box-shadow: 0 8px 25px rgba(79, 70, 229, 0.5) !important;
            background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%) !important;
        }

        /* Form Reset */
        [data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_styling()

# --- CONTENT LAYOUT ---
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.write("<div style='height: 30vh;'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div style='padding-left: 15%;'>
            <div style='background: #6366f1; width: 40px; height: 4px; border-radius: 10px; margin-bottom: 20px;'></div>
            <h1 style='color: white; font-size: 52px; font-weight: 700; line-height: 1.1; letter-spacing: -2px;'>
                TenderFlow<br><span style='color: #6366f1;'>Intelligence.</span>
            </h1>
            <p style='color: #9ca3af; font-size: 18px; margin-top: 20px; font-weight: 400;'>
                Proprietary AI for procurement<br>and strategic sourcing.
            </p>
        </div>
    """, unsafe_allow_html=True)

with col_right:
    st.write("<div style='height: 22vh;'></div>", unsafe_allow_html=True)
    
    # Use nested columns to keep the form width professional (approx 400px)
    _, form_container, _ = st.columns([0.2, 0.6, 0.2])
    
    with form_container:
        # LOGO/HEADER
        st.markdown("""
            <div style='text-align: center; margin-bottom: 40px;'>
                <h2 style='color: white; font-size: 32px; font-weight: 700; letter-spacing: -1px; margin-bottom: 0;'>TenderFlow</h2>
                <p style='color: #6366f1; font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase;'>Secure Access Portal</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_portal"):
            # Inputs
            st.text_input("Work Email", placeholder="Work Email", label_visibility="collapsed")
            st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            
            # THE BUTTON - Centered via CSS block #4
            st.form_submit_button("Enter Portal", type="primary")

        # Optional subtle security footer
        st.markdown("<p style='text-align:center; color:#374151; font-size:10px; margin-top:50px;'>ENCRYPTED AES-256 CONNECTION</p>", unsafe_allow_html=True)