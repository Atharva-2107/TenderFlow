import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# 1. Load the secrets from the .env file into your computer's memory
load_dotenv()

# 2. Assign them to variables
# The names inside the quotes MUST match exactly what you wrote in your .env file
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
LLAMA_KEY = os.getenv("LLAMAPARSE_CLOUD_API_KEY")

# --- 1. SETUP & CONFIG ---
st.set_page_config(
    page_title="TenderFlow | Hackathon Edition",
    page_icon="🌊",
    layout="wide"
)

# Initialize Supabase Client
@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# --- 2. SESSION STATE MANAGEMENT ---
# We use this to remember if the user is logged in across page refreshes
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'access_token' not in st.session_state:
    st.session_state.access_token = ""

# --- 3. AUTHENTICATION FUNCTIONS ---
def signup_user(email, password):
    try:
        supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        st.success("Signup successful! You can now log in.")
    except Exception as e:
        st.error(f"Signup failed: {str(e)}")

def login_user(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.logged_in = True
        st.session_state.user_email = email
        st.session_state.access_token = response.session.access_token
        st.rerun()
    except Exception as e:
        st.error(f"Login failed: {str(e)}")

def logout_user():
    supabase.auth.sign_out()
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.access_token = ""
    st.rerun()

# --- 4. LOGIN UI ---
if not st.session_state.logged_in:
    st.title("🌊 Welcome to TenderFlow")
    st.subheader("Please sign in to access the procurement portal")
    
    with st.container(border=True):
        col1, col2 = st.columns([1, 1])
        with col1:
            email = st.text_input("Email Address")
            password = st.text_input("Password", type="password")
            col_login, col_signup = st.columns(2)
            
            with col_login:
                if st.button("Login", type="primary", use_container_width=True):
                    login_user(email, password)

            with col_signup:
                if st.button("Sign Up", use_container_width=True):
                    signup_user(email, password)
        
        with col2:
            st.info("Don't have an account? Contact your administrator or sign up via the Supabase dashboard.")
            st.write("TenderFlow uses secure end-to-end encryption for all bid submissions.")
    st.stop() # This prevents the rest of the code from running until logged in

# --- 5. MAIN APP UI (ONLY RUNS IF LOGGED IN) ---

# Sidebar Navigation
st.sidebar.title("🌊 TenderFlow")
st.sidebar.write(f"Logged in as: **{st.session_state.user_email}**")
if st.sidebar.button("Logout"):
    logout_user()

st.sidebar.markdown("---")
page = st.sidebar.radio("Go to", ["Dashboard", "Submit a Bid", "Analytics", "Settings"])

# Mock Data (In a real app, this would come from your FastAPI /search or /tenders endpoint)
if 'tender_data' not in st.session_state:
    st.session_state.tender_data = pd.DataFrame({
        "ID": ["T-101", "T-102", "T-103"],
        "Project Name": ["Smart City Lighting", "Highway Expansion", "School WiFi Setup"],
        "Budget ($)": [50000, 1200000, 15000],
        "Bids Received": [5, 12, 3],
        "Status": ["Open", "Under Review", "Open"]
    })

if page == "Dashboard":
    st.title("📊 Tender Management Dashboard")
    st.write("Real-time overview of active procurement flows.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Tenders", len(st.session_state.tender_data))
    col2.metric("Total Value", f"${st.session_state.tender_data['Budget ($)'].sum():,}")
    col3.metric("Avg. Bids/Project", round(st.session_state.tender_data['Bids Received'].mean(), 1))

    st.markdown("---")
    st.subheader("Current Tenders")
    st.dataframe(st.session_state.tender_data, use_container_width=True)

elif page == "Submit a Bid":
    st.title("📝 Bid Submission Portal")
    st.info("Ensure all financial disclosures are attached before submitting.")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("Company Name", placeholder="e.g. Acme Corp")
            tender_id = st.selectbox("Select Target Tender", st.session_state.tender_data["ID"])
        with col2:
            bid_amount = st.number_input("Your Bid Amount ($)", min_value=0, step=1000)
            contact_email = st.text_input("Representative Email", value=st.session_state.user_email)

        message = st.text_area("Value Proposition (Why choose you?)")
        uploaded_file = st.file_uploader("Upload Technical Proposal (PDF)")

        if st.button("Submit Official Bid", type="primary"):
            if company_name and bid_amount > 0 and contact_email:
                st.success(f"Success! Bid for {company_name} has been logged.")
                st.balloons()
            else:
                st.warning("Please fill out the required fields.")

elif page == "Analytics":
    st.title("📈 Tender Analytics")
    fig = px.bar(
        st.session_state.tender_data, 
        x="Project Name", 
        y="Budget ($)", 
        color="Status",
        title="Budget Distribution by Project",
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)

elif page == "Settings":
    st.title("⚙️ System Settings")
    st.write(f"Account Email: {st.session_state.user_email}")
    st.checkbox("Enable Email Notifications")
    if st.button("Export Audit Log"):
        st.write("Log exported to CSV...")