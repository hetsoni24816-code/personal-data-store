# Home.py

# --- Initialize DB schema before anything else ---
from db_init import init_schema
try:
    init_schema()  # safe to call every run
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

# ---------- Header ----------
st.title("🔒 Personal Data Store Platform")

st.write(
    """
    Welcome to the **Personal Data Store (PDS)** platform.  
    Our mission is to give individuals **full control over their personal data**.  
    You can securely upload, manage, and share datasets with organisations you trust — 
    all while ensuring transparency and rewards for responsible data use.
    """
)

st.markdown("### 🌟 What we do")
st.markdown(
    """
    - **Secure Data Storage** — Your data is encrypted at rest.  
    - **Permission Management** — You decide which organisations can access it.  
    - **Consent & Transparency** — Every action is logged for accountability.  
    - **Rewards System** — Organisations earn credits when they access your data responsibly.  
    """
)

# ---------- Call to action ----------
st.divider()
st.markdown("👉 Get started by logging in or creating an account:")

st.page_link("pages/0_Login.py", label="🔐 Login / Sign Up", icon="🔑")

st.divider()
st.caption("Built for privacy, security, and trust.")
