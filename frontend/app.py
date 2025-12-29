import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
import extra_streamlit_components as stx

# 1. PAGE CONFIG - MUST BE FIRST
st.set_page_config(page_title="TenderFlow", page_icon="🌊", layout="wide")

# 2. LOAD ENVIRONMENT
# Path(__file__).parent is 'frontend', .parent.parent is the root 'TENDERFLOW'
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

@st.cache_resource
def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    # This prevents the Pylance 'None' error by ensuring strings exist
    if not url or not key:
        st.error(f"Credentials not found at {env_path.absolute()}")
        st.stop()
        
    return create_client(url, key)

supabase = get_supabase()

# 3. SESSION STATE INITIALIZATION
# Not logged in → intro
if not st.session_state.get("authenticated"):
    st.switch_page("pages/introductory_page.py")
    st.stop()

# Logged in but onboarding not finished → resume onboarding
if not st.session_state.get("onboarding_complete", False):
    st.switch_page("pages/informationCollection.py")
    st.stop()

# Fully onboarded → dashboard
st.switch_page("pages/dashboard.py")