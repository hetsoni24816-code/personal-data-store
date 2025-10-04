# pages/3_Consent_log.py
"""
Consent Log (Admin)
- Admin-only view of access_logs with filters
- Joined with users + datasets for readability
- CSV export
- Pagination, caching, timezone toggle, and optional "Only my datasets"
"""

# --- import shim (allow importing from project root) ---
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# -------------------------------------------------------

import json
from datetime import datetime, timedelta, date, timezone
import pandas as pd
import streamlit as st

from db import get_conn

# ---------------- Page config & sidebar theme ----------------
st.set_page_config(page_title="Consent log", page_icon="📜", layout="wide")
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] { background-color: #0D2847; color: white; }
        [data-testid="stSidebar"] * { color: white !important; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Consent Log")

# ---------------- Auth gate ----------------
uid = st.session_state.get("uid")
role = st.session_state.get("role")

if not uid:
    st.warning("Please log in first (see **Login / Sign Up** page).")
    st.stop()

# ---- Admin-only gate ----
if role != "admin":
    st.info("This page is restricted to administrators.")
    st.stop()

# ---------------- Helpers ----------------
LOCAL_TZ = "Pacific/Auckland"  # Adjust if needed

@st.cache_data(ttl=60)
def _distinct_vals(col: str) -> list[str]:
    with get_conn() as conn:
        rows = conn.execute(f"SELECT DISTINCT {col} FROM access_logs ORDER BY {col} ASC").fetchall()
    return [r[0] for r in rows if r and r[0]]

def _safe_json_compact(s: str | None) -> str:
    if not s:
        return ""
    try:
        obj = json.loads(s)
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return s

def _safe_json_pretty(s: str | None) -> str:
    if not s:
        return ""
    try:
        obj = json.loads(s)
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return s

def _default_start() -> date:
    # last 30 days (UTC)
    return (datetime.now(timezone.utc) - timedelta(days=30)).date()

@st.cache_data(ttl=30)
def _query_logs(
    start_d: date,
    end_d: date,
    roles: list[str],
    actions: list[str],
    q: str | None,
    only_owner_id: int | None,
    limit: int,
    offset: int,
):
    where = ["1=1"]
    params: list = []

    # Date window (stored in UTC text; DATE() is fine)
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

    if only_owner_id is not None:
        where.append("COALESCE(d.owner_id,-1) = ?")
        params.append(int(only_owner_id))

    if q:
        where.append(
            "("
            "  COALESCE(d.name,'') LIKE ? OR "
            "  COALESCE(a.name,'') LIKE ? OR "
            "  COALESCE(a.email,'') LIKE ? OR "
            "  COALESCE(l.meta,'') LIKE ?"
            ")"
        )
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
    LIMIT ? OFFSET ?
    """
    params_with_paging = params + [int(limit), int(offset)]

    with get_conn() as conn:
        rows = conn.execute(sql, params_with_paging).fetchall()

        # Also return a quick total count for pagination controls (approximate w/o OFFSET)
        cnt_sql = f"SELECT COUNT(1) FROM access_logs l LEFT JOIN datasets d ON d.id=l.dataset_id LEFT JOIN users a ON a.id=l.actor_id WHERE {' AND '.join(where)}"
        total = conn.execute(cnt_sql, params).fetchone()[0]

    cols = [
        "timestamp","action","actor_role","actor_id","actor_name","actor_email",
        "dataset_id","dataset_name","dataset_owner_id","meta_raw"
    ]
    df = pd.DataFrame(rows, columns=cols)
    return df, int(total)

def _to_local(dt_series: pd.Series, tz_name: str) -> pd.Series:
    try:
        # Access logs 'at' column is naive UTC text. Localize to UTC then convert.
        s = pd.to_datetime(dt_series, errors="coerce", utc=True)
        return s.dt.tz_convert(tz_name)
    except Exception:
        return dt_series

# ---------------- Filters UI ----------------
with st.container(border=True):
    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        start_d = st.date_input("From date", value=_default_start(), format="YYYY-MM-DD", key="cl_from")
    with c2:
        end_d = st.date_input("To date", value=date.today(), format="YYYY-MM-DD", key="cl_to")
    with c3:
        limit = st.selectbox("Rows per page", options=[100, 200, 500, 1000], index=0)

    roles_all   = _distinct_vals("actor_role")
    actions_all = _distinct_vals("action")

    c4, c5, c6 = st.columns([2, 3, 3])
    with c4:
        roles_sel = st.multiselect("Actor roles", options=roles_all, default=roles_all)
    with c5:
        actions_sel = st.multiselect("Actions", options=actions_all, default=actions_all)
    with c6:
        q = st.text_input("Search (dataset/user/meta)", placeholder="e.g., grant, denied, org@example.com, scope=...")

    c7, c8, c9 = st.columns([2, 2, 2])
    with c7:
        only_mine = st.checkbox("Only my datasets", value=False, help="Filter to entries where you are the dataset owner.")
    with c8:
        pretty_meta = st.checkbox("Pretty-print meta JSON", value=False)
    with c9:
        tz_local = st.checkbox("Show times in local timezone", value=True, help=f"Local timezone: {LOCAL_TZ}")

# Guard invalid dates
if isinstance(start_d, date) and isinstance(end_d, date) and start_d > end_d:
    st.error("From date must be earlier than or equal to To date.")
    st.stop()

# ---------------- Pagination state ----------------
page = st.number_input("Page", min_value=1, value=1, step=1)
offset = (page - 1) * int(limit)

# ---------------- Query + format ----------------
owner_filter = uid if only_mine else None
df, total_rows = _query_logs(start_d, end_d, roles_sel, actions_sel, q, owner_filter, int(limit), int(offset))

if df.empty:
    st.info("No log entries match your filters.")
    st.stop()

# Convert timestamps if requested
if tz_local:
    df["timestamp"] = _to_local(df["timestamp"], LOCAL_TZ)

# Meta formatting
if pretty_meta:
    df["meta"] = df["meta_raw"].map(_safe_json_pretty)
else:
    df["meta"] = df["meta_raw"].map(_safe_json_compact)
df.drop(columns=["meta_raw"], inplace=True)

# ---------------- Metrics ----------------
with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows (this page)", len(df))
    c2.metric("Total rows (all pages)", total_rows)
    c3.metric("Unique datasets", df["dataset_id"].nunique())
    top_action = df["action"].value_counts().idxmax() if not df.empty else "-"
    c4.metric("Top action", top_action)

# ---------------- Table ----------------
st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------- CSV export ----------------
csv = df.to_csv(index=False).encode("utf-8")
ts_suffix = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
st.download_button(
    "⬇️ Download this page as CSV",
    data=csv,
    file_name=f"consent_log_page_{int(page)}_{ts_suffix}.csv",
    mime="text/csv",
)

# ---------------- Action counts (this page) ----------------
with st.expander("See action counts (this page)"):
    cnt = df.groupby("action").size().reset_index(name="count").sort_values("count", ascending=False)
    st.bar_chart(cnt.set_index("action"))
