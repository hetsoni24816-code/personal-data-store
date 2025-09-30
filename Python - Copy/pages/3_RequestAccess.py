# pages/3_RequestAccess.py
"""
Org: Request access to datasets & download approved data
- Only for users with role='org'
- Browse discoverable datasets (Trusted/Public) not owned by you
- Request access with optional message (logs 'request_access')
- See status of requests
- Download datasets you already have access to (Trusted+granted or Public)
"""

# --- import shim (allow importing from project root) ---
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# -------------------------------------------------------

import streamlit as st
from db import get_conn
from permissions import request_access, list_my_requests
from storage import get_dataset_for_download

# ---- gate & role ----
uid = st.session_state.get("uid")
role = st.session_state.get("role")
if not uid:
    st.set_page_config(page_title="Request Access", page_icon="📨", layout="wide")
    st.warning("Please log in first (see **Login / Sign Up**).")
    st.stop()
if role != "org":
    st.set_page_config(page_title="Request Access", page_icon="📨", layout="wide")
    st.info("This page is for organisations. Log in with an organisation account to request access.")
    st.stop()

st.set_page_config(page_title="Request Access", page_icon="📨", layout="wide")
st.title("📨 Request Access")

# ---- Discoverable datasets (Trusted/Public from other owners) ----
st.subheader("Discover datasets")
with get_conn() as conn:
    discover = conn.execute(
        """
        SELECT d.id, d.name, u.name AS owner_name, d.visibility, d.created_at
        FROM datasets d
        JOIN users u ON u.id = d.owner_id
        WHERE d.visibility IN ('Trusted','Public')
          AND d.owner_id != ?
        ORDER BY d.created_at DESC
        LIMIT 200
        """,
        (uid,),
    ).fetchall()

if not discover:
    st.info("No discoverable datasets yet.")
else:
    for (ds_id, name, owner_name, vis, ts) in discover:
        with st.container(border=True):
            st.markdown(f"**{name}** · {vis} · by **{owner_name}** · {ts}")
            msg = st.text_input(
                "Optional message to owner",
                key=f"msg_{ds_id}",
                placeholder="Why do you need this data?"
            )
            col_btn, _ = st.columns([1, 4])
            with col_btn:
                if vis == "Public":
                    st.caption("Public dataset — request not required.")
                if st.button("Request access", key=f"req_{ds_id}"):
                    try:
                        request_access(dataset_id=ds_id, org_id=uid, message=msg)
                        st.success("Request sent.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")

# ---- My request statuses ----
st.subheader("My requests")
reqs = list_my_requests(uid)  # (dataset_id, dataset_name, owner_id, status, ts)
if not reqs:
    st.caption("No requests yet.")
else:
    for (ds_id, name, owner_id, status, ts) in reqs:
        st.write(f"- [{ts}] **{name}** — status: **{status}**")

# ---- Datasets I can access (Public or Trusted+granted) ----
st.subheader("Datasets I can access")
with get_conn() as conn:
    accessible = conn.execute(
        """
        SELECT d.id, d.name, u.name AS owner_name, d.visibility, d.created_at
        FROM datasets d
        JOIN users u ON u.id = d.owner_id
        WHERE d.owner_id != ?
          AND (
            d.visibility = 'Public'
            OR (
              d.visibility = 'Trusted'
              AND EXISTS (
                SELECT 1 FROM permissions p
                WHERE p.dataset_id = d.id
                  AND p.org_id = ?
                  AND p.allow = 1
                  AND p.status = 'granted'
                  AND (p.expires_at IS NULL OR p.expires_at >= DATE('now'))
              )
            )
          )
        ORDER BY d.created_at DESC
        LIMIT 200
        """,
        (uid, uid),
    ).fetchall()

if not accessible:
    st.caption("No datasets available to download yet.")
else:
    for (ds_id, name, owner_name, vis, ts) in accessible:
        with st.container(border=True):
            st.markdown(f"**{name}** · {vis} · by **{owner_name}** · {ts}")
            try:
                data, fname, mime = get_dataset_for_download(
                    dataset_id=ds_id,
                    actor_id=uid,
                    actor_role=role,
                    purpose="download",
                )
                st.download_button(
                    "⬇️ Download",
                    data=data,
                    file_name=fname,
                    mime=mime,
                    key=f"dl_{ds_id}",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Cannot download: {e}")
