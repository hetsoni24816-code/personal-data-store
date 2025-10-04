# pages/3_Consent_log.py
"""
Consent Log (Admin)
- Admin-only view of access_logs with rich filters
- Joined with users + datasets for readability
- CSV export
- Pagination (Next/Prev), caching, timezone toggle, "Only my datasets"
- Quick date presets & quick actor filters
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
        .btn-row > div > button { width: 100% !important; }
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

if role != "admin":
    st.info("This page is restricted to administrators.")
    st.stop()

# ---------------- Helpers ----------------
LOCAL_TZ = "Pacific/Auckland"  # Adjust if needed

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _default_start() -> date:
    return (_now_utc() - timedelta(days=30)).date()

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

def _to_local(dt_series: pd.Series, tz_name: str) -> pd.Series:
    try:
        s = pd.to_datetime(dt_series, errors="coerce", utc=True)
        return s.dt.tz_convert(tz_name)
    except Exception:
        return dt_series

@st.cache_data(ttl=30, show_spinner=False)
def _query_logs(
    start_d: date,
    end_d: date,
    roles: list[str],
    actions: list[str],
    q_text: str | None,
    actor_name_q: str | None,
    actor_email_q: str | None,
    only_owner_id: int | None,
    limit: int,
    offset: int,
):
    where = ["1=1"]
    params: list = []

    # Dates
    if isinstance(start_d, date):
        where.append("DATE(l.at) >= DATE(?)")
        params.append(start_d.isoformat())
    if isinstance(end_d, date):
        where.append("DATE(l.at) <= DATE(?)")
        params.append(end_d.isoformat())

    # Roles & actions
    if roles:
        where.append(f"l.actor_role IN ({','.join('?' for _ in roles)})")
        params.extend(roles)
    if actions:
        where.append(f"l.action IN ({','.join('?' for _ in actions)})")
        params.extend(actions)

    # Owner filter
    if only_owner_id is not None:
        where.append("COALESCE(d.owner_id,-1) = ?")
        params.append(int(only_owner_id))

    # General search
    if q_text:
        like = f"%{q_text}%"
        where.append(
            "("
            "  COALESCE(d.name,'') LIKE ? OR "
            "  COALESCE(a.name,'') LIKE ? OR "
            "  COALESCE(a.email,'') LIKE ? OR "
            "  COALESCE(l.meta,'') LIKE ?"
            ")"
        )
        params.extend([like, like, like, like])

    # Specific actor quick filters
    if actor_name_q:
        where.append("COALESCE(a.name,'') LIKE ?")
        params.append(f"%{actor_name_q}%")
    if actor_email_q:
        where.append("COALESCE(a.email,'') LIKE ?")
        params.append(f"%{actor_email_q}%")

    sql_base = f"""
    FROM access_logs l
    LEFT JOIN users    a ON a.id = l.actor_id
    LEFT JOIN datasets d ON d.id = l.dataset_id
    WHERE {' AND '.join(where)}
    """

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
    {sql_base}
    ORDER BY l.at DESC, l.id DESC
    LIMIT ? OFFSET ?
    """
    params_with_paging = params + [int(limit), int(offset)]

    with get_conn() as conn:
        rows = conn.execute(sql, params_with_paging).fetchall()
        total = conn.execute(f"SELECT COUNT(1) {sql_base}", params).fetchone()[0]

    cols = [
        "timestamp","action","actor_role","actor_id","actor_name","actor_email",
        "dataset_id","dataset_name","dataset_owner_id","meta_raw"
    ]
    df = pd.DataFrame(rows, columns=cols)
    return df, int(total)

# ---------------- Filter controls ----------------
with st.container(border=True):
    left, right = st.columns([3, 2])

    with left:
        c1, c2, c3 = st.columns([1.2, 1.2, 0.6])
        with c1:
            start_d = st.date_input("From", value=_default_start(), format="YYYY-MM-DD", key="cl_from")
        with c2:
            end_d = st.date_input("To", value=date.today(), format="YYYY-MM-DD", key="cl_to")
        with c3:
            limit = st.selectbox("Rows/page", options=[100, 200, 500, 1000], index=0)

        # Quick presets
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            if st.button("Last 7d"):
                st.session_state["cl_from"] = (_now_utc() - timedelta(days=7)).date()
                st.session_state["cl_page"] = 1
        with p2:
            if st.button("Last 30d"):
                st.session_state["cl_from"] = (_now_utc() - timedelta(days=30)).date()
                st.session_state["cl_page"] = 1
        with p3:
            if st.button("Last 90d"):
                st.session_state["cl_from"] = (_now_utc() - timedelta(days=90)).date()
                st.session_state["cl_page"] = 1
        with p4:
            if st.button("Today"):
                st.session_state["cl_from"] = date.today()
                st.session_state["cl_to"] = date.today()
                st.session_state["cl_page"] = 1

        roles_all   = _distinct_vals("actor_role")
        actions_all = _distinct_vals("action")

        c4, c5 = st.columns(2)
        with c4:
            roles_sel = st.multiselect("Actor roles", options=roles_all, default=roles_all)
        with c5:
            actions_sel = st.multiselect("Actions", options=actions_all, default=actions_all)

        c6, c7 = st.columns(2)
        with c6:
            actor_name_q = st.text_input("Actor name contains", placeholder="e.g., Acme")
        with c7:
            actor_email_q = st.text_input("Actor email contains", placeholder="e.g., org@")

        q_text = st.text_input(
            "Search anywhere (dataset/user/meta)",
            placeholder="e.g., grant, denied, scope=agg-only, dataset.csv"
        )

        c8, c9, c10 = st.columns(3)
        with c8:
            only_mine = st.checkbox("Only my datasets", value=False, help="Show entries where you are the dataset owner.")
        with c9:
            pretty_meta = st.checkbox("Pretty-print meta JSON", value=False)
        with c10:
            tz_local = st.checkbox("Show local timezone", value=True, help=f"Local timezone: {LOCAL_TZ}")

    with right:
        st.markdown("#### Actions")
        ar, rr = st.columns(2)
        with ar:
            reset = st.button("Reset filters", type="secondary")
        with rr:
            refresh = st.button("Refresh", type="primary")

        if reset:
            for k in ("cl_from", "cl_to", "cl_page"):
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

        if refresh:
            st.cache_data.clear()
            st.rerun()

# Guard invalid dates
if isinstance(start_d, date) and isinstance(end_d, date) and start_d > end_d:
    st.error("From date must be earlier than or equal to To date.")
    st.stop()

# ---------------- Pagination state ----------------
if "cl_page" not in st.session_state:
    st.session_state["cl_page"] = 1

page = st.number_input("Page", min_value=1, value=int(st.session_state["cl_page"]), step=1)
if page != st.session_state["cl_page"]:
    st.session_state["cl_page"] = int(page)

offset = (st.session_state["cl_page"] - 1) * int(limit)

# ---------------- Query + format ----------------
owner_filter = uid if only_mine else None
df, total_rows = _query_logs(
    start_d, end_d,
    roles_sel, actions_sel,
    q_text, actor_name_q, actor_email_q,
    owner_filter, int(limit), int(offset)
)

if df.empty:
    st.info("No log entries match your filters.")
    st.stop()

# Convert timestamps if requested
if tz_local:
    df["timestamp"] = _to_local(df["timestamp"], LOCAL_TZ)

# Meta formatting
df["meta"] = (df["meta_raw"].map(_safe_json_pretty) if pretty_meta
              else df["meta_raw"].map(_safe_json_compact))
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
    file_name=f"consent_log_page_{int(st.session_state['cl_page'])}_{ts_suffix}.csv",
    mime="text/csv",
)

# ---------------- Pagination controls ----------------
total_pages = max(1, (total_rows + int(limit) - 1) // int(limit))
st.caption(f"Page {int(st.session_state['cl_page'])} of {total_pages}")

prev_col, next_col, spacer = st.columns([1, 1, 8], gap="small")
with prev_col:
    if st.button("◀ Prev", disabled=st.session_state["cl_page"] <= 1):
        st.session_state["cl_page"] -= 1
        st.rerun()
with next_col:
    if st.button("Next ▶", disabled=st.session_state["cl_page"] >= total_pages):
        st.session_state["cl_page"] += 1
        st.rerun()

# ---------------- Action counts (this page) ----------------
with st.expander("See action counts (this page)"):
    cnt = df.groupby("action").size().reset_index(name="count").sort_values("count", ascending=False)
    st.bar_chart(cnt.set_index("action"))
