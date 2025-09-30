# pages/1_UploadData.py
"""
📂 Upload Data
- Requires login
- Accepts CSV / JSON / TXT (≤10MB)
- Validates, encrypts, versions, and stores file (storage.save_dataset)
- Lists your latest uploads with secure download + visibility controls
"""

# --- import shim so pages/ can import project-root modules ---
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ----------------------------------------------------------------

import json
import streamlit as st

from storage import (
    save_dataset,
    list_my_latest,
    list_versions,
    get_dataset_for_download,  # secure + audited (+ rewards when orgs download)
    change_visibility,
)

# ------------------ Gate: require login ------------------
uid = st.session_state.get("uid")
role = st.session_state.get("role")
name = st.session_state.get("name", "")
if not uid:
    st.set_page_config(page_title="Upload Data", page_icon="📂", layout="wide")
    st.warning("Please log in first (see **Login / Sign Up**).")
    st.stop()

st.set_page_config(page_title="Upload Data", page_icon="📂", layout="wide")
st.title("📂 Upload Data")
st.caption(f"Logged in as **{name}** ({role})")

# ------------------ Config ------------------
ALLOWED_EXTS = {"csv", "json", "txt"}
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
VIS_OPTS = ["Private", "Trusted", "Public"]

def _ext(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""

# ------------------ Validators ------------------
def _validate_csv(raw: bytes) -> tuple[bool, str]:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return False, "CSV must be UTF-8 text."
    lines = text.splitlines()
    if not lines:
        return False, "CSV is empty."
    if ("," not in lines[0]) and ("\t" not in lines[0]) and (";" not in lines[0]):
        return False, "CSV header not detected (no delimiter found)."
    return True, ""

def _validate_json(raw: bytes) -> tuple[bool, str]:
    try:
        json.loads(raw.decode("utf-8"))
        return True, ""
    except UnicodeDecodeError:
        return False, "JSON must be UTF-8 text."
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e.msg}"

def _validate_txt(raw: bytes) -> tuple[bool, str]:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return False, "TXT must be UTF-8 text."
    if not text.strip():
        return False, "TXT is empty."
    return True, ""

def _validate_file(file_name: str, raw: bytes, size_hint: int | None) -> tuple[bool, str]:
    if size_hint is not None and size_hint > MAX_BYTES:
        return False, f"File is too large (> {MAX_BYTES // (1024*1024)} MB)."
    if not raw:
        return False, "No file data."
    if len(raw) > MAX_BYTES:
        return False, f"File is too large (> {MAX_BYTES // (1024*1024)} MB)."
    ext = _ext(file_name)
    if ext not in ALLOWED_EXTS:
        return False, f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTS))}"
    if ext == "csv":
        return _validate_csv(raw)
    if ext == "json":
        return _validate_json(raw)
    if ext == "txt":
        return _validate_txt(raw)
    return False, "Unsupported extension."

# ------------------ Upload UI ------------------
with st.container(border=True):
    st.subheader("Add a new file")
    uploaded = st.file_uploader(
        "Choose a CSV / JSON / TXT file",
        type=list(ALLOWED_EXTS),
        key="ud_file",
    )

    col_left, col_right = st.columns([3, 1])
    with col_left:
        desc = st.text_area(
            "Short description",
            placeholder="e.g., March step count export from my phone",
            key="ud_desc",
        )
    with col_right:
        visibility = st.selectbox(
            "Default visibility",
            VIS_OPTS,
            index=0,
            key="ud_vis",
            help="Use Trusted if orgs should be able to request access.",
        )

    if uploaded:
        st.info(f"Selected: **{uploaded.name}** · size: {uploaded.size:,} bytes")
        raw = uploaded.read()
        ok, msg = _validate_file(uploaded.name, raw, uploaded.size)
        if not ok:
            st.error(f"Validation failed: {msg}")
        else:
            preview = raw[:800].decode("utf-8", errors="ignore")
            with st.expander("Preview (first 800 characters)"):
                st.code(preview or "(no printable text)")

            if st.button("Upload securely", type="primary", use_container_width=True, key="ud_submit"):
                try:
                    ds_id, ver = save_dataset(
                        owner_id=uid,
                        file_name=uploaded.name,
                        mime=uploaded.type or "application/octet-stream",
                        raw_bytes=raw,
                        description=desc,
                        visibility=visibility,
                    )
                    st.success(f"Uploaded **{uploaded.name}** as version **v{ver}** ({visibility}).")
                    st.rerun()
                except Exception as e:
                    st.error(f"Upload failed: {e}")
    else:
        st.caption("Accepted types: .csv, .json, .txt · Max size: 10 MB · Files are encrypted at rest.")

# ------------------ My latest uploads ------------------
st.subheader("My latest uploads")
rows = list_my_latest(uid)  # (id, name, version, visibility, created_at)

if not rows:
    st.info("No uploads yet. Add your first file above.")
else:
    for (ds_id, name_f, ver, vis, ts) in rows:
        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 3, 2])
            c1.markdown(f"**{name_f}**")
            c2.markdown(f"Version: **v{ver}**")
            c3.markdown(f"Visibility: **{vis}**")
            c4.markdown(f"Uploaded: {ts}")

            # Secure download (permission check + audit + reward is inside storage)
            try:
                data_bytes, dl_name, dl_mime = get_dataset_for_download(
                    dataset_id=ds_id,
                    actor_id=uid,
                    actor_role=role,
                    purpose="download",
                )
                c5.download_button(
                    "Download",
                    data=data_bytes,
                    file_name=dl_name,
                    mime=dl_mime,
                    key=f"dl_{ds_id}",
                    use_container_width=True,
                )
            except Exception as e:
                # PermissionError is already logged as denied; owners still always allowed
                c5.write(f"🔒 {e}")

            # Inline visibility update
            cc1, cc2 = st.columns([4, 1])
            new_vis = cc1.selectbox(
                "Change visibility",
                VIS_OPTS,
                index=VIS_OPTS.index(vis) if vis in VIS_OPTS else 0,
                key=f"vis_sel_{ds_id}",
            )
            if cc2.button("Update", key=f"vis_btn_{ds_id}", use_container_width=True):
                try:
                    ok_update = change_visibility(owner_id=uid, dataset_id=ds_id, new_visibility=new_vis)
                    if ok_update:
                        st.success(f"Visibility updated to {new_vis}.")
                        st.rerun()
                    else:
                        st.error("Could not update visibility (not owner or dataset missing).")
                except Exception as e:
                    st.error(f"Update failed: {e}")

            # Version history
            with st.expander("See version history"):
                vers = list_versions(uid, name_f)  # (id, version, visibility, created_at)
                if not vers:
                    st.write("No versions found.")
                else:
                    for (_id, _v, _vis, _ts) in vers:
                        st.write(f"- id={_id} · v{_v} · {_vis} · {_ts}")
