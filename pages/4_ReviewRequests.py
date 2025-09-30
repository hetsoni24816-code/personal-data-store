# pages/4_ReviewRequests.py
"""
Owner: Review and approve/deny organisation requests
- Shows pending requests for datasets owned by current user
- Approve -> set permissions.allow=1, status='granted'
- Deny   -> set permissions.allow=0, status='revoked'
- Logs 'grant' / 'revoke' / 'permissions_update'
"""

# --- import shim (allow importing from project root) ---
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# -------------------------------------------------------

import streamlit as st
from datetime import date
from permissions import list_pending_requests_for_owner, approve_request, deny_request

# ---- Gate: require login ----
uid = st.session_state.get("uid")
if not uid:
    st.set_page_config(page_title="Review Requests", page_icon="🗂️", layout="wide")

    # Custom Sidebar Styles
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
        </style>
        """,
        unsafe_allow_html=True
    )

    st.warning("Please log in first (see **Login / Sign Up**).")
    st.stop()

st.set_page_config(page_title="Review Requests", page_icon="🗂️", layout="wide")

# Custom Sidebar Styles
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
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Review Access Requests")

# ---- Fetch pending requests ----
rows = list_pending_requests_for_owner(uid)  # (dataset_id, dataset_name, org_id, org_name, requested_at)
if not rows:
    st.info("No pending requests at this time.")
    st.stop()

for (ds_id, ds_name, org_id, org_name, req_at) in rows:
    with st.container(border=True):
        st.markdown(f"**{ds_name}** · requested by **{org_name}** (org #{org_id}) · {req_at}")

        # Approve / Deny controls
        c1, c2 = st.columns([2, 2])
        with c1:
            scope = st.text_input(
                "Grant scope (optional)",
                key=f"scope_{ds_id}_{org_id}",
                placeholder="e.g. agg-only,no-ads"
            )
        with c2:
            exp = st.date_input(
                "Expiry (optional)",
                value=None,
                format="YYYY-MM-DD",
                key=f"exp_{ds_id}_{org_id}"
            )
            exp_iso = exp.isoformat() if isinstance(exp, date) else None

        colA, colB, _ = st.columns([1, 1, 4])
        with colA:
            if st.button("✅ Approve", type="primary", key=f"approve_{ds_id}_{org_id}"):
                try:
                    approve_request(
                        dataset_id=ds_id,
                        owner_id=uid,
                        org_id=org_id,
                        scope=(scope.strip() or None),
                        expires_at=exp_iso,
                    )
                    st.success(f"Approved access for {org_name}.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to approve: {e}")
        with colB:
            deny_reason = st.text_input(
                "Reason (optional)",
                key=f"deny_reason_{ds_id}_{org_id}",
                placeholder="Why denying?"
            )
            if st.button("❌ Deny", key=f"deny_{ds_id}_{org_id}"):
                try:
                    deny_request(
                        dataset_id=ds_id,
                        owner_id=uid,
                        org_id=org_id,
                        reason=(deny_reason.strip() or None),
                    )
                    st.warning(f"Denied access for {org_name}.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to deny: {e}")
