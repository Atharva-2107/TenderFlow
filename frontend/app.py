import streamlit as st
from pages.introductory_page import intro_page
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


st.set_page_config(
    page_title="TenderFlow",
    layout="centered",
    initial_sidebar_state="collapsed"
)

if "page" not in st.session_state:
    st.session_state.page = "intro"

# Initialize Supabase Client
@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

if st.session_state.page == "intro":
    intro_page()
    
elif st.session_state.page == "login":
    st.title("🔐 Login Page")

elif st.session_state.page == "signup":
    st.title("✨ Sign Up Page")

elif st.session_state.page == "dashboard":
    st.title("📊 Dashboard")