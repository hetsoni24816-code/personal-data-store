# pages/2_ManagePermissions.py
"""
Manage Permissions
- Requires login
- Pick one of your datasets (latest version per filename)
- Change visibility: Private | Trusted | Public
- Add/remove trusted organisations (role='org', verified=1)
"""

# -------------------------- Imports & setup --------------------------
import sys, pathlib, time
from datetime import date
import streamlit as st

# ---- HARD GUARD: exit if not launched via `streamlit run`
def _ensure_streamlit_context_or_exit():
    try:
        # Streamlit >= 1.28
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx() is None:
            print("This page must be launched with: streamlit run pages/2_ManagePermissions.py")
            sys.exit(0)
    except Exception:
        # Fallback for older/newer versions
        try:
            # If this exists and returns Falsey, also exit
            if hasattr(st, "runtime") and hasattr(st.runtime, "exists") and not st.runtime.exists():
                print("This page must be launched with: streamlit run pages/2_ManagePermissions.py")
                sys.exit(0)
        except Exception:
            # If we can't verify, do nothing; running with `python` will still fail gracefully below
            pass

_ensure_streamlit_context_or_exit()

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storage import list_my_latest, change_visibility
from permissions import (
    list_org_directory,
    list_trusted_org_ids,
    set_trusted_orgs,          # bulk add/remove + logs 'permissions_update'
    update_permission_details  # optional per-org scope/expiry update
)

NOW = lambda: time.strftime("%Y-%m-%d %H:%M:%S")

# -------------------------- App config -------------------------------
st.set_page_config(page_title="Manage Permissions", page_icon="🔐", layout="wide")

# Sidebar theming
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] { background-color: #0D2847; color: white; }
        [data-testid="stSidebar"] * { color: white !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------- Auth gate --------------------------------
uid = st.session_state.get("uid")
if not uid:
    st.warning("Please log in first (see **Login / Sign Up**).")
    st.stop()

st.title("Manage Permissions")
st.caption(f"Logged in as **{st.session_state.get('name','')}**")

# -------------------------- Helpers ----------------------------------
def safe_first(seq, default=None):
    return seq[0] if seq else default

def dataset_rows_for_user(user_id: int):
    """Rows: (id, name, version, visibility, created_at)"""
    try:
        return list_my_latest(user_id)
    except Exception as e:
        st.error(f"Could not load your datasets: {e}")
        return []

def build_dataset_label(row):
    _id, name, ver, vis, ts = row
    return f"{name}  (v{ver}) — {vis} — {ts}"

# -------------------------- Dataset selection ------------------------
rows = dataset_rows_for_user(uid)
if not rows:
    st.info("You have no datasets yet. Upload a file first in **Upload Data**.")
    st.stop()

ds_labels = [build_dataset_label(r) for r in rows]
ds_id_by_label = {label: rows[i][0] for i, label in enumerate(ds_labels)}

selected_label = st.selectbox(
    "Select a dataset",
    options=ds_labels,
    index=0,
    key="mp_ds_select",
)

# Defensive fallback
if selected_label is None:
    selected_label = safe_first(ds_labels)

if not selected_label:
    st.warning("Please select a dataset.")
    st.stop()

dataset_id = ds_id_by_label.get(selected_label)
if dataset_id is None:
    # Extra fallback: take first row’s id
    dataset_id = rows[0][0]

current_row = next((r for r in rows if r[0] == dataset_id), None)
if current_row is None:
    # Final fallback: use first row
    current_row = rows[0]

ds_name, ds_ver, ds_vis, ds_ts = current_row[1], current_row[2], current_row[3], current_row[4]

# -------------------------- Visibility controls ----------------------
with st.container(border=True):
    st.subheader("Dataset visibility")
    st.write(f"**{ds_name}**  ·  Latest version: **v{ds_ver}**  ·  Uploaded: {ds_ts}")

    vis_options = ["Private", "Trusted", "Public"]
    vis_index = vis_options.index(ds_vis) if ds_vis in vis_options else 0

    new_vis = st.selectbox(
        "Visibility",
        options=vis_options,
        index=vis_index,
        key="mp_vis_select",
    )

    left, right = st.columns([1, 5])
    with left:
        if st.button("Update visibility", key="mp_vis_btn"):
            try:
                ok = change_visibility(owner_id=uid, dataset_id=dataset_id, new_visibility=new_vis)
                if ok:
                    st.success(f"Visibility updated to {new_vis}.")
                    st.rerun()
                else:
                    st.error("Could not update visibility (are you the owner?).")
            except Exception as e:
                st.error(f"Update failed: {e}")

    with right:
        if new_vis == "Private":
            st.info("Only you can access this dataset.")
        elif new_vis == "Public":
            st.warning("Anyone with access to your profile/app can view this dataset.")
        else:
            st.caption("Trusted: only organisations you select below may access this dataset.")

# -------------------------- Trusted organisations --------------------
with st.container(border=True):
    st.subheader("Trusted organisations")

    try:
        orgs = list_org_directory()  # [(id, name, email), ...]
    except Exception as e:
        orgs = []
        st.error(f"Could not load organisation directory: {e}")

    if not orgs:
        st.info("No verified organisations are available yet.")
    else:
        org_labels = [f"{name}  <{email}>" for (oid, name, email) in orgs]
        org_id_by_label = {org_labels[i]: orgs[i][0] for i in range(len(orgs))}

        try:
            current_trusted_ids = set(list_trusted_org_ids(dataset_id))
        except Exception as e:
            current_trusted_ids = set()
            st.error(f"Could not load current trusted orgs: {e}")

        default_org_labels = [lbl for lbl, oid in org_id_by_label.items() if oid in current_trusted_ids]

        sel_org_labels = st.multiselect(
            "Select which organisations may access this dataset when visibility = Trusted",
            options=org_labels,
            default=default_org_labels,
            key="mp_trusted_ms",
        )
        chosen_org_ids = [org_id_by_label[lbl] for lbl in sel_org_labels]

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
            default_expires_iso = exp.isoformat() if isinstance(exp, date) else None

        col_a, col_b, _col_spacer = st.columns([1, 1, 6])
        with col_a:
            if st.button("Save trusted orgs", type="primary", key="mp_trusted_save"):
                try:
                    summary = set_trusted_orgs(
                        dataset_id=dataset_id,
                        owner_id=uid,
                        new_org_ids=chosen_org_ids,
                        default_scope=(scope.strip() or None),
                        default_expires_at=default_expires_iso,
                    )
                    added = summary.get("added") or []
                    removed = summary.get("removed") or []
                    st.success(f"Trusted orgs updated. Added: {added or 'none'} · Removed: {removed or 'none'}.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Update failed: {e}")

        with col_b:
            if st.button("Reload", key="mp_trusted_reload"):
                st.rerun()

        with st.expander("Edit scope/expiry for a specific organisation", expanded=False):
            base_ids = chosen_org_ids or list(current_trusted_ids)
            if not base_ids:
                st.caption("No trusted organisations yet.")
            else:
                name_by_id = {oid: name for (oid, name, email) in orgs}
                id_options = [(oid, name_by_id.get(oid, f"Org {oid}")) for oid in base_ids]

                opt_labels = [f"{oid} — {nm}" for oid, nm in id_options]
                chosen_label = st.selectbox("Choose org", options=opt_labels, key="mp_edit_org_sel")

                sel_org_id = None
                if chosen_label:
                    try:
                        sel_org_id = int(chosen_label.split(" — ")[0])
                    except Exception:
                        sel_org_id = None

                col1, col2, col3 = st.columns([2, 2, 2])
                with col1:
                    scope_u = st.text_input("Scope", key="mp_edit_scope", placeholder="e.g. agg-only,no-ads")
                with col2:
                    exp_u = st.date_input("Expiry", value=None, format="YYYY-MM-DD", key="mp_edit_expiry")
                with col3:
                    st.markdown("&nbsp;")
                    if st.button("Save details", key="mp_edit_save"):
                        if sel_org_id is None:
                            st.error("Please select a valid organisation.")
                        else:
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

# -------------------------- Footer -----------------------------------
st.caption("All permission changes (visibility & trusted orgs) are logged to the consent log.")
