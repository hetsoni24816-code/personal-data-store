# Home.py (Healthcare-focused with visible slogan)

# --- Initialize DB schema before anything else ---
from db_init import init_schema
try:
    init_schema()  # idempotent; safe every run
except Exception as e:
    import streamlit as st  # local import to avoid failing before st is available
    st.error(f"DB init failed: {e}")

import streamlit as st

# ---------- Page config & sidebar styling ----------
st.set_page_config(page_title="Personal Data Store", page_icon=None, layout="wide")
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            background-color: #0D2847; /* dark blue */
            color: white;
        }
        [data-testid="stSidebar"] * { color: white !important; }

        .slogan {
            text-align: center;
            font-size: 1.8rem;
            font-weight: 700;
            margin: 0.5rem 0 1rem 0;
            background: linear-gradient(90deg, #0077FF, #00C4A7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .card { border-radius: 16px; padding: 1.2rem 1.1rem; box-shadow: 0 6px 24px rgba(0,0,0,0.08); border: 1px solid rgba(13,40,71,0.12); }
        .subtle { color: #2E3A48; }
        .muted { color: #566173; }
        .pill { display: inline-block; padding: 0.25rem 0.6rem; border-radius: 999px; border: 1px solid rgba(13,40,71,0.18); font-size: 0.85rem; margin-right: 0.35rem; }
        .ok { background: #F3FAF5; }
        .warn { background: #FFF9F1; }
        .pub { background: #F3F7FF; }
        .step { font-weight: 600; }
        .hr { height: 1px; background: rgba(13,40,71,0.12); margin: 1rem 0 1.25rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Main content ----------
st.title("Personal Data Store Platform")

st.markdown('<div class="slogan">Your Health Data. Your Control. Your Benefit.</div>', unsafe_allow_html=True)

st.write(
    """
    Take control of your **healthcare data**. Securely upload lab results, wearable exports, GP visit notes, or wellness logs; set the privacy level for each dataset; and earn when organisations download your data with permission.
    """
)

# Value props in three cards
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        """
        <div class="card">
            <h3>Upload Healthcare Data</h3>
            <p class="subtle">Bring your own data from clinics, devices, or files. Everything is encrypted at rest and tracked with an audit trail.</p>
            <div class="hr"></div>
            <p class="muted">Supported examples: blood tests (PDF/CSV), heart-rate logs (CSV), step and sleep exports, consultation summaries, imaging reports (file metadata only).</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        """
        <div class="card">
            <h3>Privacy Controls per Dataset</h3>
            <p class="subtle">Choose how each dataset can be discovered and accessed:</p>
            <p><span class="pill ok">Private</span> Visible only to you.</p>
            <p><span class="pill warn">Trusted</span> Visible to approved organisations you whitelist.</p>
            <p><span class="pill pub">Public</span> Discoverable by verified organisations; access still requires permission checks.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        """
        <div class="card">
            <h3>Rewards & Payouts</h3>
            <p class="subtle">Earn <strong>1 point</strong> for every organisation that downloads your dataset with permission. Points convert to <strong>$0.10 NZD per download</strong>.</p>
            <div class="hr"></div>
            <p class="muted">Redemptions and reporting are shown in your Rewards page. All downloads are permission-checked and logged.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# How organisations use data
st.subheader("How organisations use your data")
st.write(
    """
    Verified organisations (e.g., universities, research labs, healthcare providers, or insurers offering wellness incentives) can request access to your datasets for **research, analytics, or service improvement**. You approve or deny each request. When approved, their download is **recorded in the audit log**, your dataset version is referenced, and your **reward is credited automatically**.
    """
)

# How it works steps
st.subheader("How it works")
st.markdown(
    """
    1. <span class="step">Upload</span> your healthcare data files. Add a short description and set the privacy to **Private**, **Trusted**, or **Public**.
    2. <span class="step">Review requests</span> from organisations. Approve only those you trust.
    3. <span class="step">Earn</span> when approved organisations download your dataset: **1 point = $0.10 NZD** per download.
    4. <span class="step">Track</span> everything in the audit log—who accessed what, when, and why.
    """,
    unsafe_allow_html=True,
)

# Transparency & security blurb
st.markdown(
    """
    <div class="card">
        <h3>Security & Transparency</h3>
        <p class="muted">Data is encrypted at rest; permission checks are enforced for every download; and a complete audit trail is maintained. You can change a dataset's privacy level at any time.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Navigation button ----------
st.markdown("---")
if st.button("Go to Login / Sign Up", use_container_width=True):
    st.switch_page("pages/0_Login.py")