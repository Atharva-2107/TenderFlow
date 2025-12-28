import streamlit as st
import base64
import os
from pathlib import Path

def get_base64_of_bin_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def render_navbar():
    # Directory where this file (navbar.py) is located: frontend/components
    current_dir = Path(__file__).parent

    # Go up one level to frontend/ and into assets/logo.png
    logo_path = current_dir.parent / "assets" / "logo.png"

    logo_base64 = get_base64_of_bin_file(str(logo_path))
    
    # Logic for the logo image tag
    logo_html = f'<img src="data:image/png;base64,{logo_base64}">' if logo_base64 else '<h3 style="color:white; margin:0;">TenderFlow</h3>'

    navbar_html = f"""
    <style>
        /* HIDE DEFAULT STREAMLIT HEADER */
        header {{ visibility: hidden; }}
        .stApp > header {{ display: none; }}
    
        /* ADJUST PADDING FOR MAIN CONTENT */
        .block-container {{
            padding-top: 3.5rem !important;
        }}

        /* NAVBAR STYLING */
        .navbar-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 70px;
            background-color: #111827;
            border-bottom: 1px solid #374151;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 25px;
            z-index: 999999;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}

        .navbar-logo img {{
            height: 65px;
            width: auto;
            margin-top: 6px;
        }}

        /* PROFILE BUTTON STYLING */
        .navbar-profile-btn {{
            background-color: #1F2937;
            border: 1px solid #374151;
            color: #E5E7EB;
            padding: 8px 18px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .navbar-profile-btn:hover {{
            background-color: #374151;
            border-color: #4B5563;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }}
    </style>

    <div class="navbar-container">
        <div class="navbar-logo">
            {logo_html}
        </div>
        <div class="navbar-right">
            <button class="navbar-profile-btn" onclick="showProfileMenu()">
                👤 Person A
            </button>
        </div>
    </div>

    <script>
    function showProfileMenu() {{
        // Add your profile dropdown logic here
        alert('Profile menu opened!');
    }}
    </script>
    """
    st.markdown(navbar_html, unsafe_allow_html=True)