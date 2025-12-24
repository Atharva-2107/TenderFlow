import streamlit as st
from pages.introductory_page import intro_page

st.set_page_config(
    page_title="TenderFlow",
    layout="centered",
    initial_sidebar_state="collapsed"
)

if "page" not in st.session_state:
    st.session_state.page = "intro"


if st.session_state.page == "intro":
    intro_page()
    
elif st.session_state.page == "login":
    st.title("🔐 Login Page")

elif st.session_state.page == "signup":
    st.title("✨ Sign Up Page")

elif st.session_state.page == "dashboard":
    st.title("📊 Dashboard")