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
            background-color: #0D2847;
            color: white;
        }
        [data-testid="stSidebar"] * { color: white !important; }

        /* Layout + typography */
        .slogan {
            font-size: 28px;
            font-weight: 800;
            color: #0D2847;
            text-align: center;
            margin: 16px 0 28px 0;
        }
        .slogan .highlight { color: #0078FF; }

        .content {
            max-width: 900px;
            margin: 0 auto;
            line-height: 1.6;
            color: #e5e7eb; /* light text for dark themes */
        }
        .content p { color: #d1d5db; font-size: 17px; }
        .content ul { margin: 10px 0 10px 20px; }
        .content li { margin: 6px 0; }
        .content strong { color: #ffffff; }

        .button-wrap { text-align: center; margin-top: 24px; }
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

# IMPORTANT: no leading spaces inside <div>, and use pure HTML (no **markdown**)
st.markdown(
    """
<div class="content">

<p>The Personal Data Store (PDS) Platform enables individuals to securely upload their
healthcare data—such as medical reports, fitness records, or wellness metrics—into an
encrypted personal vault.</p>

<p>Organisations (e.g., research institutes and health technology companies) can request
access to these datasets to develop better healthcare solutions and innovations.</p>

<p>You have complete control over the privacy of every dataset you upload:</p>
<ul>
  <li><strong>Private</strong> — Only you can access it.</li>
  <li><strong>Trusted</strong> — Only the approved organisations you select can view and use it.</li>
  <li><strong>Public</strong> — Share openly to support global healthcare research.</li>
</ul>

<p>Each time an organisation downloads your dataset, you earn <strong>1 reward point</strong>
(worth <strong>$0.10</strong>). Rewards accumulate over time, so you benefit directly from
contributing to healthcare advancement.</p>

<p>All actions—uploads, permission changes, access requests, downloads, and rewards—are
securely logged for transparency and accountability.</p>

<div class="button-wrap">
</div>
</div>
    """,
    unsafe_allow_html=True
)

# ---------- Navigation button ----------
# Put the button after the HTML so Streamlit renders it as a native widget
if st.button("Go to Login / Sign Up", use_container_width=True):
    st.switch_page("pages/0_Login.py")
