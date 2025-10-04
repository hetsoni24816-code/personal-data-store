# Home.py

# --- Initialize DB schema before anything else ---
from db_init import init_schema
try:
    init_schema()  # idempotent; safe every run
except Exception as e:
    import streamlit as st
    st.error(f"DB init failed: {e}")

import streamlit as st

# ---------- Page config & sidebar styling ----------
st.set_page_config(page_title="Personal Data Store", page_icon="🔒", layout="wide")
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            background-color: #0D2847; /* dark blue */
            color: white;
        }
        [data-testid="stSidebar"] * { color: white !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Main content ----------
st.title("Personal Data Store Platform")

st.write(
    """
    Welcome to the Personal Data Store (PDS) Platform.

    Our platform empowers individuals to take control of their personal data.
    - Users can securely upload and manage their own datasets.  
    - Organisations can request access to user data for research or services.  
    - Admins oversee transparency through logs and audit tools.  

    Data is encrypted at rest, and every action — from uploads to permissions —
    is logged for accountability and trust.
    """
)

# ---------- Navigation button ----------
st.markdown("---")
if st.button("Go to Login / Sign Up", use_container_width=True):
    st.switch_page("pages/0_Login.py")
