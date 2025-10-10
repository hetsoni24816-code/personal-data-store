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

        /* Page styling */
        .slogan {
            font-size: 30px;
            font-weight: 800;
            color: #0D2847;
            text-align: center;
            margin-top: 20px;
            margin-bottom: 40px;
        }
        .slogan .highlight { color: #0078FF; }

        .content {
            max-width: 900px;
            margin: 0 auto;
            line-height: 1.6;
            color: #1E1E1E; /* dark grey text for light background */
            font-size: 17px;
        }
        .content p {
            color: #222222;
            font-size: 17px;
            text-align: justify;
        }
        .content ul {
            margin: 10px 0 10px 25px;
            color: #222222;
        }
        .content li {
            margin: 6px 0;
        }
        .content strong {
            color: #0D2847;
        }

        .button-wrap {
            text-align: center;
            margin-top: 35px;
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
<div class="content">

<p>The Personal Data Store (PDS) Platform empowers individuals to securely upload their
healthcare data — such as medical reports, fitness records, or wellness metrics — into an
encrypted personal vault.</p>

<p>Organisations such as research institutes and health technology companies can request
access to these datasets to develop better healthcare solutions and innovations.</p>

<p>You have full control over the privacy of each dataset you upload:</p>
<ul>
  <li><strong>Private</strong> — Only you can access it.</li>
  <li><strong>Trusted</strong> — Approved organisations you choose can view and use it.</li>
  <li><strong>Public</strong> — Share openly to support global healthcare research.</li>
</ul>

<p>Each time an organisation downloads your dataset, you earn <strong>1 reward point</strong>
(worth <strong>$0.10</strong>). These rewards accumulate over time, giving you a direct
benefit from supporting healthcare progress.</p>

<p>Every action — upload, access, and reward — is securely logged to ensure transparency and trust.</p>

</div>
    """,
    unsafe_allow_html=True
)

# ---------- Navigation button ----------
st.markdown('<div class="button-wrap">', unsafe_allow_html=True)
if st.button("Go to Login / Sign Up", use_container_width=False):
    st.switch_page("pages/0_Login.py")
st.markdown('</div>', unsafe_allow_html=True)
