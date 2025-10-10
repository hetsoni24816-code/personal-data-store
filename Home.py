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
        [data-testid="stSidebar"] * {
            color: white !important;
        }

        /* Slogan styling */
        .slogan {
            font-size: 28px;
            font-weight: 700;
            color: #0D2847;
            text-align: center;
            margin-top: 20px;
            margin-bottom: 40px;
        }

        .highlight {
            color: #0078FF;
        }

        .subtext {
            font-size: 17px;
            color: #333333;
            line-height: 1.6;
            margin-left: 10%;
            margin-right: 10%;
            text-align: justify;
        }

        .button-container {
            text-align: center;
            margin-top: 40px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Main content ----------
st.title("Personal Data Store Platform")

st.markdown(
    """
    <div class="slogan">
        <span class="highlight">Your Health Data.</span> 
        <span class="highlight">Your Control.</span> 
        <span class="highlight">Your Benefit.</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="subtext">
        The Personal Data Store (PDS) Platform allows individuals to **securely upload their healthcare data** — 
        such as medical reports, fitness records, or wellness metrics — into an encrypted personal vault.  

        Organisations such as research institutes or health technology companies can then **request access** 
        to these datasets to develop better healthcare solutions and innovations.  

        You have complete control over the privacy of your data:
        <ul>
            <li><b>Private</b> – Only you can access it.</li>
            <li><b>Trusted</b> – Approved organisations you select can view and use it.</li>
            <li><b>Public</b> – Share openly to support global healthcare research.</li>
        </ul>

        Each time an organisation downloads your dataset, you earn <b>1 reward point</b> 
        (worth <b>$0.10</b>). These rewards can accumulate over time, giving you 
        tangible benefits for contributing to healthcare advancement.  

        Every action — upload, access, and reward — is securely logged and fully transparent.
    </div>
    """,
    unsafe_allow_html=True
)

# ---------- Navigation button ----------
st.markdown('<div class="button-container">', unsafe_allow_html=True)
if st.button("Go to Login / Sign Up", use_container_width=False):
    st.switch_page("pages/0_Login.py")
st.markdown('</div>', unsafe_allow_html=True)
