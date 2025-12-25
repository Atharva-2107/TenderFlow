import os
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# --- 1. IMPORT YOUR CUSTOM PAGES ---
# This looks into your pages folder and grabs the intro_page function
from pages.introductory_page import intro_page
import extra_streamlit_components as stx

# --- 2. INITIALIZATION & SECRETS ---
# Load secrets from the root folder
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

# Fetch Keys from Environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
LLAMA_KEY = os.getenv("LLAMAPARSE_CLOUD_API_KEY")
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="TenderFlow",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Cookie Manager for "Stay Logged In"
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

# Initialize Supabase Client
@st.cache_resource
def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("⚠️ Environment variables not found. Check your .env file!")
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# --- 2. SESSION STATE MANAGEMENT ---
if 'page' not in st.session_state:
    st.session_state.page = "intro" # Default starting page
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None


# Attempt to recover session from cookies on startup
token = cookie_manager.get(cookie="tf_access_token")
if token and not st.session_state.authenticated and supabase:
    try:
        # Recover session using the token
        res = supabase.auth.set_session(token, token)
        st.session_state.authenticated = True
        st.session_state.user = res.user
        st.session_state.page = "dashboard" # Jump to dashboard if cookie found
    except:
        cookie_manager.delete("tf_access_token")

# --- 4. AUTHENTICATION LOGIC ---
# def login_user(email, password):
#     try:
#         res = supabase.auth.sign_in_with_password({"email": email, "password": password})
#         st.session_state.authenticated = True
#         st.session_state.user = res.user
#         # Save token to browser (expires in 7 days)
#         cookie_manager.set("tf_access_token", res.session.access_token, key="login_cookie")
#         st.session_state.page = "dashboard"
#         st.rerun()
#     except Exception as e:
#         st.error(f"Login failed: {str(e)}")

def logout_user():
    if supabase:
        supabase.auth.sign_out()
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.page = "intro"
    cookie_manager.delete("tf_access_token", key="logout_cookie")
    st.rerun()

# --- 5. ROUTING LOGIC ---

# 1. Introductory Page (Imported from introductory_page.py)
if st.session_state.page == "intro":
    intro_page()

# 2. Login Page
elif st.session_state.page == "login":
    st.switch_page("pages/loginPage.py")
    # st.title("🔐 Login to TenderFlow")
    # with st.form("login_form"):
    #     email = st.text_input("Email")
    #     password = st.text_input("Password", type="password")
    #     if st.form_submit_button("Sign In", type="primary"):
    #         login_user(email, password)
    
    # if st.button("Don't have an account? Sign Up"):
    #     st.session_state.page = "signup"
    #     st.rerun()
    # if st.button("← Back to Intro"):
    #     st.session_state.page = "intro"
    #     st.rerun()

# 3. Sign Up Page
elif st.session_state.page == "signup":
    st.title("✨ Create Account")
    with st.form("signup_form"):
        new_email = st.text_input("Email")
        new_pass = st.text_input("Password", type="password")
        if st.form_submit_button("Create Account"):
            try:
                supabase.auth.sign_up({"email": new_email, "password": new_pass})
                st.success("Check your email for the confirmation link!")
            except Exception as e:
                st.error(str(e))
    
    if st.button("Already have an account? Login"):
        st.session_state.page = "login"
        st.rerun()

# 4. Main Dashboard (Protected Content)
elif st.session_state.page == "dashboard":
    if not st.session_state.authenticated:
        st.session_state.page = "login"
        st.rerun()

    # Sidebar for Dashboard Navigation
    st.sidebar.title("🌊 TenderFlow")
    st.sidebar.write(f"Logged in: {st.session_state.user.email}")
    if st.sidebar.button("Logout"):
        logout_user()
    
    st.sidebar.divider()
    sub_page = st.sidebar.radio("Navigation", ["Overview", "Company Profile", "Tender Analysis", "Bid Submission"])

    if sub_page == "Overview":
        st.title("📊 Procurement Dashboard")
        
        try:
            requests.get(f"{API_URL}/")
            st.sidebar.success("● Backend Online")
        except:
            st.sidebar.warning("○ Backend Offline")

        col1, col2, col3 = st.columns(3)
        col1.metric("Active Tenders", "12")
        col2.metric("Total Value", "$1.2M")
        col3.metric("Bids in Progress", "4")

    elif sub_page == "Company Profile":
        st.title("🏢 Company Profile")
        st.text_input("Company Name")
        st.file_uploader("Upload Past Performance (Excel)", type=['xlsx'])
        if st.button("Sync with AI"):
            st.info("Processing data mapping...")

    elif sub_page == "Tender Analysis":
        st.title("🔍 AI Tender Analysis")
        st.file_uploader("Upload New Tender PDF", type=['pdf'])
        if st.button("Run LlamaParse"):
            st.write("Connecting to FastAPI backend...")

    elif sub_page == "Bid Submission":
        st.title("📝 Bid Submission")
        st.write("Fill out the submission form below.")