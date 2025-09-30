# pages/3_Consent_log.py
"""
Consent Log
- Requires login
- Shows entries from access_logs with filters
- Joined with users + datasets for readability
- CSV export
"""

# --- import shim (allow importing from project root) ---
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# -------------------------------------------------------

import json
from datetime import datetime, timedelta, date
import streamlit as st
import pandas as pd

from db import get_conn

# ---------------- Gate: require login ----------------
uid = st.session_state.get("uid")
if not uid:
    st.set_page_config(page_title="Consent log", page_icon="📜", layout="wide")

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

    st.warning("Please log in first (see **Login / Sign Up** page).")
    st.stop()

st.set_page_config(page_title="Consent log", page_icon="📜", layout="wide")

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

st.title("Consent Log")

# ---------------- Helpers ----------------
def _load_distinct(col: str) -> list[str]:
    with get_conn() as conn:
        rows = conn.execute(f"SELECT DISTINCT {col} FROM access_logs ORDER BY {col} ASC").fetchall()
    return [r[0] for r in rows if r and r[0]]

def _safe_json_str(s: str | None) -> str:
    if not s:
        return ""
    try:
        obj = json.loads(s)
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return s

def _default_start():
    return (datetime.utcnow() - timedelta(days=30)).date()

# ---------------- Filters UI ----------------
with st.container(border=True):
    col1, col2, col3 = st.columns([2,2,2])
    with col1:
        start_d = st.date_input("From date", value=_default_start(), format="YYYY-MM-DD", key="cl_from")
    with col2:
        end_d   = st.date_input("To date", value=date.today(), format="YYYY-MM-DD", key="cl_to")
    with col3:
        limit   = st.selectbox("Max rows", options=[100, 200, 500, 1000, 5000], index=2)

    roles_all   = _load_distinct("actor_role")
    actions_all = _load_distinct("action")

    col4, col5, col6 = st.columns([2,3,3])
    with col4:
        roles = st.multiselect("Actor roles", options=roles_all, default=roles_all)
    with col5:
        actions = st.multiselect("Actions", options=actions_all, default=actions_all)
    with col6:
        q = st.text_input("Search (dataset/user/meta)", placeholder="e.g., grant, denied, org@example.com, scope=...")

# ---------------- Build query ----------------
where = ["1=1"]
params: list = []

if isinstance(start_d, date):
    where.append("DATE(l.at) >= DATE(?)")
    params.append(start_d.isoformat())
if isinstance(end_d, date):
    where.append("DATE(l.at) <= DATE(?)")
    params.append(end_d.isoformat())

if roles:
    where.append(f"l.actor_role IN ({','.join('?' for _ in roles)})")
    params.extend(roles)

if actions:
    where.append(f"l.action IN ({','.join('?' for _ in actions)})")
    params.extend(actions)

if q:
    where.append("(COALESCE(d.name,'') LIKE ? OR COALESCE(a.name,'') LIKE ? OR COALESCE(a.email,'') LIKE ? OR COALESCE(l.meta,'') LIKE ?)")
    like = f"%{q}%"
    params.extend([like, like, like, like])

sql = f"""
SELECT
    l.at                    AS timestamp,
    l.action                AS action,
    l.actor_role            AS actor_role,
    a.id                    AS actor_id,
    a.name                  AS actor_name,
    a.email                 AS actor_email,
    d.id                    AS dataset_id,
    d.name                  AS dataset_name,
    d.owner_id              AS dataset_owner_id,
    l.meta                  AS meta_raw
FROM access_logs l
LEFT JOIN users    a ON a.id = l.actor_id
LEFT JOIN datasets d ON d.id = l.dataset_id
WHERE {' AND '.join(where)}
ORDER BY l.at DESC, l.id DESC
LIMIT ?
"""
params_with_limit = params + [int(limit)]

# ---------------- Query + format ----------------
with get_conn() as conn:
    rows = conn.execute(sql, params_with_limit).fetchall()

if not rows:
    st.info("No log entries match your filters.")
    st.stop()

df = pd.DataFrame(rows, columns=[
    "timestamp","action","actor_role","actor_id","actor_name","actor_email",
    "dataset_id","dataset_name","dataset_owner_id","meta_raw"
])

df["meta"] = df["meta_raw"].map(_safe_json_str)
df.drop(columns=["meta_raw"], inplace=True)

# Quick counts at the top
with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", len(df))
    c2.metric("Unique datasets", df["dataset_id"].nunique())
    c3.metric("Unique actors", df["actor_id"].nunique())
    top_action = df["action"].value_counts().idxmax() if not df.empty else "-"
    c4.metric("Top action", top_action)

# Display table
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

# CSV export
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download CSV",
    data=csv,
    file_name=f"consent_log_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv",
    use_container_width=False,
)

with st.expander("See action counts"):
    cnt = df.groupby("action").size().reset_index(name="count").sort_values("count", ascending=False)
    st.bar_chart(cnt.set_index("action"))
