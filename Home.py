# Home.py

# --- Initialize DB schema before anything else ---
from db_init import init_schema
try:
    init_schema()  # idempotent; safe every run
except Exception as e:
    import streamlit as st  # local import to avoid failing before st is available
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

# ---------- Session info ----------
uid  = st.session_state.get("uid")
role = st.session_state.get("role", "-")
name = st.session_state.get("name", "")

# ---------- Header ----------
st.title("🔒 Personal Data Store Platform")

if uid:
    st.caption(f"Logged in as **{name or 'Unknown'}** · role: **{role}**")
else:
    st.warning("You’re not logged in. Use **Login / Sign Up** in the sidebar.")

st.write("Use the links below to navigate:")

# ---------- Navigation (role-aware) ----------
st.markdown("### 📂 Data & Permissions")
st.page_link("pages/1_UploadData.py", label="Upload Data — add datasets securely")
st.page_link("pages/2_ManagePermissions.py", label="Manage Permissions — control access")

st.markdown("### 🏆 Rewards")
st.page_link("pages/5_RewardsSummary.py", label="Rewards Summary — see credits earned")

# Org-only tools
st.markdown("### 🏢 Organisation Tools")
st.page_link("pages/3_RequestAccess.py", label="Request Access — browse & request datasets")

# Owner review (any user who owns datasets can use this)
st.markdown("### 🗂️ Owner Review")
st.page_link("pages/4_ReviewRequests.py", label="Review Requests — approve or deny org requests")

# Admin-only
if role == "admin":
    st.markdown("### 🛡️ Admin")
    st.page_link("pages/3_Consent_log.py", label="Consent Log (Admin) — audit access & actions")

# ---------- Helpful notes ----------
st.divider()
st.caption(
    "Data is encrypted at rest. All actions (uploads, grants, downloads, rewards) "
    "are recorded in the audit log for transparency."
)
