# import streamlit as st

# # --- PAGE SETUP ---
# st.set_page_config(page_title=" Information", layout="wide")

# # --- PROFESSIONAL DARK THEME CSS ---
# st.markdown("""
#     <style>
#     @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

#     /* Dark Premium Background */
#     .stApp {
#         background: radial-gradient(circle at 20% 30%, #1a1c4b 0%, #0f111a 100%);
#         font-family: 'Inter', sans-serif;
#         color: #e0e0e0;
#     }

#     /* Reduce top spacing */
#     .block-container {
#         padding-top: 2rem !important;
#     }

#     /* Title Styling */
#     .header-text {
#         text-align: center;
#         margin-bottom: 25px;
#     }
#     .header-text h1 {
#         font-size: 38px;
#         font-weight: 600;
#         color: #ffffff;
#         margin-bottom: 5px;
#     }
#     .header-text p {
#         color: #8888b2;
#         font-size: 16px;
#     }

#     /* Input Box Widths */
#     .stTextInput, .stSelectbox, .stTextArea, .stFileUploader {
#         max-width: 500px;
#         margin: 0 auto;
#     }

#     /* Label Styling */
#     label {
#         color: #bbbbff !important;
#         font-weight: 500 !important;
#     }

#     /* Custom Input Box Look */
#     div[data-baseweb="input"], div[data-baseweb="select"], .stTextArea textarea {
#         background-color: rgba(255, 255, 255, 0.05) !important;
#         border: 1px solid rgba(255, 255, 255, 0.1) !important;
#         border-radius: 8px !important;
#         color: white !important;
#     }

#     /*
#        SUBMIT BUTTON SPECIFIC STYLING (CENTERED)
#      */
#     .stButton {
#         display: flex;
#         justify-content: center;
#         margin-top: 20px;
#     }

#     div.stButton > button {
#         background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
#         color: white !important;
#         border: none !important;
#         padding: 12px 0px !important;
#         border-radius: 10px !important; /* Pill shape like your image */
#         font-size: 18px !important;
#         font-weight: 600 !important;
#         width: 320px !important; /* Fixed width to ensure it stays centered */
#         transition: all 0.3s ease !important;
#         box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
#     }

#     div.stButton > button:hover {
#         transform: scale(1.03) !important;
#         box-shadow: 0 0 25px rgba(99, 102, 241, 0.5) !important;
#     }

#     /* Hide Streamlit Branding */
#     header, footer {visibility: hidden;}
#     </style>
#     """, unsafe_allow_html=True)

# # --- LOCK LOGIC ---
# if 'authenticated' not in st.session_state:
#     st.session_state.authenticated = False

# if not st.session_state.authenticated:
#     st.markdown("""
#         <div class="header-text">
#             <h1>Complete Your Profile</h1>
#             <p>Please provide your details to access the dashboard</p>
#         </div>
#     """, unsafe_allow_html=True)

#     # Main outer centering
#     _, mid, _ = st.columns([1, 1.5, 1])

#     with mid:
#         # Keep upper part
#         u_name = st.text_input("Full Name", placeholder="e.g. John Doe")
#         c_name = st.text_input("Company Name", placeholder="e.g. Acme Corp")
#         email = st.text_input("Email Address", placeholder="name@company.com")
        
#         # --- NEW SECTION: PHONE TILL LAST ---
#         c1, c2 = st.columns(2)
#         with c1:
#             phone = st.text_input("Phone Number",placeholder="Enter Phone Number", max_chars=10, help="Exactly 10 digits required")
#         with c2:
#             role = st.selectbox("Your Role", ["Select Role", "Admin", "Financial analysist", "Bid Manager", "Technical person", "Other"])
            
#         address = st.text_area("Company Address", placeholder="Street, City, Zip Code", height=150)
        
#         st.markdown("<div style='margin-top:20px;'><b>Upload Portfolio/Profile</b> (PDF or Excel, Max 20MB)</div>", unsafe_allow_html=True)
#         uploaded_file = st.file_uploader("", type=['pdf', 'xlsx', 'xls'], label_visibility="collapsed")

#         # --- SEPARATE BUTTON CENTERING LOGIC ---
#         # We use nested columns here to create a "container" for the button in the middle
#         st.write("") # Extra spacing
#         btn_spacer_left, btn_center, btn_spacer_right = st.columns([0.5, 1, 0.5])
        
#         with btn_center:
#             if st.button("Unleash the Magic 🚀"):
#                 if not (u_name and c_name and email and phone and address and uploaded_file):
#                     st.error("⚠️ All fields are compulsory!")
#                 elif len(phone) < 10 or not phone.isdigit():
#                     st.error("⚠️ Please enter a valid 10-digit phone number.")
#                 elif role == "Select Role":
#                     st.error("⚠️ Please select your role.")
#                 elif uploaded_file.size > 20 * 1024 * 1024:
#                     st.error("⚠️ File size exceeds 20MB.")
#                 else:
#                     st.session_state.authenticated = True
#                     st.success("Verification Successful!")
#                     st.rerun()

#     st.stop()

# # --- MAIN APP CONTENT ---
# st.title("Protected Dashboard")
# st.write(f"Welcome back! You are now viewing the internal data.")


import streamlit as st

# --- PAGE SETUP ---
st.set_page_config(page_title="Information", layout="wide")

# --- PROFESSIONAL DARK THEME CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    .stApp {
        background: radial-gradient(circle at 20% 30%, #1a1c4b 0%, #0f111a 100%);
        font-family: 'Inter', sans-serif;
        color: #e0e0e0;
    }

    .block-container {
        padding-top: 2rem !important;
    }

    .header-text {
        text-align: center;
        margin-bottom: 25px;
    }
    .header-text h1 {
        font-size: 38px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 5px;
    }

    /* FIX: Apply width to the container, not individual inputs */
    [data-testid="column"] > div > div > div {
        max-width: 500px;
        margin: 0 auto;
    }

    /* Standardize all input widths to fill their containers */
    .stTextInput, .stSelectbox, .stTextArea, .stFileUploader {
        width: 100% !important;
    }

    label {
        color: #bbbbff !important;
        font-weight: 500 !important;
    }

    div[data-baseweb="input"], div[data-baseweb="select"], .stTextArea textarea {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: white !important;
    }

    .stButton {
        display: flex;
        justify-content: center;
        margin-top: 20px;
    }

    div.stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
        color: white !important;
        border: none !important;
        padding: 12px 0px !important;
        border-radius: 10px !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        width: 320px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
    }

    header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- LOCK LOGIC ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
        <div class="header-text">
            <h1>Complete Your Profile</h1>
            <p>Please provide your details to access the dashboard</p>
        </div>
    """, unsafe_allow_html=True)

    # Use one main column to center the entire form
    _, mid, _ = st.columns([1, 2, 1])

    with mid:
        st.text_input("Full Name", placeholder="e.g. John Doe")
        st.text_input("Company Name", placeholder="e.g. Acme Corp")
        st.text_input("Email Address", placeholder="name@company.com")
        
        # This creates the side-by-side row
        col1, col2 = st.columns(2)
        with col1:
            phone = st.text_input("Phone Number", placeholder="Enter Phone Number", max_chars=10)
        with col2:
            role = st.selectbox("Your Role", ["Select Role", "Admin", "Financial Analyst", "Bid Manager", "Technical Person", "Other"])
            
        st.text_area("Company Address", placeholder="Street, City, Zip Code", height=150)
        
        st.markdown("<div style='margin-top:20px;'><b>Upload Portfolio/Profile</b></div>", unsafe_allow_html=True)
        st.file_uploader("", type=['pdf', 'xlsx', 'xls'], label_visibility="collapsed")

        if st.button("Unleash the Magic 🚀"):
            st.session_state.authenticated = True
            st.rerun()

    st.stop()

# --- MAIN APP CONTENT ---
st.title("Protected Dashboard")
st.write(f"Welcome back! You are now viewing the internal data.")