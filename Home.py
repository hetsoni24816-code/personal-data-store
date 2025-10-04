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

# ---------- Content ----------
st.title("Personal Data Store Platform")

st.markdown("""
### Who we are  
The Personal Data Store (PDS) is a secure platform that gives individuals full control over their personal information.  
We help you manage your data safely, decide who can access it, and track how it is used — all in one place.

### What we do  
- Provide a secure space to store your personal datasets.  
- Let you decide which organisations can access your information.  
- Record every action (upload, permission change, download) in an auditable consent log.  
- Reward transparency and trust between individuals and organisations.  

---

[Go to Login / Sign Up](pages/0_Login.py)
""")
