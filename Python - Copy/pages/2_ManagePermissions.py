# pages/2_ManagePermissions.py
"""
Manage Permissions
- Requires login
- Pick one of your datasets (latest version per filename)
- Change visibility: Private | Trusted | Public
- Add/remove trusted organisations (role='org', verified=1)
"""

# --- import shim: allow pages/ to import modules from project root ---
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# --------------------------------------------------------------------

import time
from datetime import date
import streamlit as st

from storage import list_my_latest, change_visibility
from permissions import (
    list_org_directory,
    list_trusted_org_ids,
    set_trusted_orgs,         # bulk add/remove + logs 'permissions_update'
    update_permission_details # optional per-org scope/expiry update
)

NOW = lambda: time.strftime("%Y-%m-%d %H:%M:%S")

# ------------------ Gate: require login ------------------
uid = st.session_state.get("uid")
if not uid:
    st.warning("Please log in first (see **Login / Sign Up**).")
    st.stop()

st.set_page_config(page_title="Manage Permissions", page_icon="🔐", layout="wide")
st.title("🔐 Manage Permissions")
st.caption(f"Logged in as **{st.session_state.get('name','')}**")

# ------------------ Select dataset ------------------
rows = list_my_latest(uid)  # (id, name, version, visibility, created_at)
if not rows:
    st.info("You have no datasets yet. Upload a file first in **Upload Data**.")
    st.stop()

labels = [f"{name}  (v{ver}) — {vis} — {ts}" for (_id, name, ver, vis, ts) in rows]
id_by_label = {lbl: rows[i][0] for i, lbl in enumerate(labels)}

selected_label = st.selectbox(
    "Select a dataset",
    options=labels,
    index=0,
    key="mp_ds_select",
)
if not selected_label:
    st.warning("Please select a dataset.")
    st.stop()

dataset_id = id_by_label[selected_label]
current_row = next((r for r in rows if r[0] == dataset_id), None)
if not current_row:
    st.error("Selected dataset not found.")
    st.stop()

ds_name, ds_ver, ds_vis, ds_ts = current_row[1], current_row[2], current_row[3], current_row[4]

# ------------------ Visibility controls ------------------
with st.container(border=True):
    st.subheader("Dataset visibility")
    st.write(f"**{ds_name}**  ·  Latest version: **v{ds_ver}**  ·  Uploaded: {ds_ts}")

    new_vis = st.selectbox(
        "Visibility",
        ["Private", "Trusted", "Public"],
        index=["Private", "Trusted", "Public"].index(ds_vis) if ds_vis in ("Private", "Trusted", "Public") else 0,
        key="mp_vis_select",
    )

    cva, cvb = st.columns([1, 5])
    with cva:
        if st.button("Update visibility", key="mp_vis_btn"):
            try:
                if change_visibility(owner_id=uid, dataset_id=dataset_id, new_visibility=new_vis):
                    st.success(f"Visibility updated to {new_vis}.")
                    st.rerun()
                else:
                    st.error("Could not update visibility (are you the owner?).")
            except Exception as e:
                st.error(f"Update failed: {e}")
    with cvb:
        if new_vis == "Private":
            st.info("Only you can access this dataset.")
        elif new_vis == "Public":
            st.warning("Anyone with access to your profile/app can view this dataset.")
        else:
            st.caption("Trusted: only organisations you select below may access this dataset.")

# ------------------ Trusted organisations ------------------
with st.container(border=True):
    st.subheader("Trusted organisations")

    orgs = list_org_directory()  # [(id, name, email), ...]
    if not orgs:
        st.info("No verified organisations are available yet.")
    else:
        # Build labels and defaults
        org_labels = [f"{name}  <{email}>" for (oid, name, email) in orgs]
        id_by_label = {org_labels[i]: orgs[i][0] for i in range(len(orgs))}
        current_trusted_ids = set(list_trusted_org_ids(dataset_id))
        default_labels = [lbl for lbl, oid in id_by_label.items() if oid in current_trusted_ids]

        sel = st.multiselect(
            "Select which organisations may access this dataset when visibility = Trusted",
            options=org_labels,
            default=default_labels,
            key="mp_trusted_ms",
        )
        chosen_ids = [id_by_label[lbl] for lbl in sel]

        # Optional defaults for new grants
        with st.expander("Optional: default policy for new grants", expanded=False):
            scope = st.text_input(
                "Default scope (comma-separated tags, e.g. agg-only,no-ads,no-LLMs)",
                key="mp_def_scope",
                placeholder="(optional)"
            )
            exp = st.date_input(
                "Default expiry date (optional)",
                value=None,
                format="YYYY-MM-DD",
                key="mp_def_expiry"
            )
            def_expiry_iso = exp.isoformat() if isinstance(exp, date) else None

        ca, cb, cc = st.columns([1, 1, 6])
        with ca:
            if st.button("Save trusted orgs", type="primary", key="mp_trusted_save"):
                try:
                    summary = set_trusted_orgs(
                        dataset_id=dataset_id,
                        owner_id=uid,
                        new_org_ids=chosen_ids,
                        default_scope=(scope.strip() or None),
                        default_expires_at=def_expiry_iso,
                    )
                    added = summary.get("added") or []
                    removed = summary.get("removed") or []
                    st.success(f"Trusted orgs updated. Added: {added or 'none'} · Removed: {removed or 'none'}.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Update failed: {e}")
        with cb:
            if st.button("Reload", key="mp_trusted_reload"):
                st.rerun()

        # Optional per-org details updater
        with st.expander("Edit scope/expiry for a specific organisation", expanded=False):
            if not current_trusted_ids and not chosen_ids:
                st.caption("No trusted organisations yet.")
            else:
                # Use current selection; if empty, use current trusted set
                base_ids = chosen_ids or list(current_trusted_ids)
                # build a dropdown with names for convenience
                name_by_id = {oid: name for (oid, name, email) in orgs}
                id_options = [(oid, name_by_id.get(oid, f"Org {oid}")) for oid in base_ids]
                if id_options:
                    opt_labels = [f"{oid} — {nm}" for oid, nm in id_options]
                    chosen_label = st.selectbox("Choose org", options=opt_labels, key="mp_edit_org_sel")
                    sel_org_id = int(chosen_label.split(" — ")[0]) if chosen_label else None

                    col1, col2, col3 = st.columns([2, 2, 2])
                    with col1:
                        scope_u = st.text_input("Scope", key="mp_edit_scope", placeholder="e.g. agg-only,no-ads")
                    with col2:
                        exp_u = st.date_input("Expiry", value=None, format="YYYY-MM-DD", key="mp_edit_expiry")
                    with col3:
                        st.markdown("&nbsp;")
                        if st.button("Save details", key="mp_edit_save"):
                            try:
                                update_permission_details(
                                    dataset_id=dataset_id,
                                    owner_id=uid,
                                    org_id=sel_org_id,
                                    scope=(scope_u.strip() or None),
                                    expires_at=(exp_u.isoformat() if isinstance(exp_u, date) else None),
                                )
                                st.success("Permission details updated.")
                            except Exception as e:
                                st.error(f"Update failed: {e}")

# Footer
st.caption("All permission changes (visibility & trusted orgs) are logged to the consent log.")
