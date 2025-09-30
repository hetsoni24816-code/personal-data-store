# pages/5_RewardsSummary.py
"""
🏆 Rewards Summary
- Requires login
- Aggregates rewards earned per dataset you own
- Schema-adaptive:
    A) rewards(amount_cents, created_at, owner_id, org_id, dataset_id, reason)
    B) rewards(amount, unit, at, meta, owner_id, org_id, dataset_id, reason)
"""

# --- import shim (allow importing from project root) ---
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# -------------------------------------------------------

import json
from datetime import date, datetime, timedelta, timezone
import pandas as pd
import streamlit as st

from db import get_conn

# ---------------- Gate: require login ----------------
uid = st.session_state.get("uid")
if not uid:
    st.set_page_config(page_title="Rewards", page_icon="🏆", layout="wide")
    st.warning("Please log in first (see **Login / Sign Up**).")
    st.stop()

st.set_page_config(page_title="Rewards", page_icon="🏆", layout="wide")
st.title("🏆 Rewards Summary")

# ---------------- Helpers ----------------
def _cols(conn, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}

def _schema(conn):
    """
    Detect which rewards schema is present and return column names to use.
    """
    c = _cols(conn, "rewards")
    if "amount_cents" in c:  # Schema A
        return {
            "amount_col": "amount_cents",
            "date_col": "created_at",
            "has_unit": False,
            "has_meta": False,
            "default_unit": "credit",
        }
    # Schema B (fallback)
    return {
        "amount_col": "amount" if "amount" in c else None,
        "date_col": "at" if "at" in c else ("created_at" if "created_at" in c else None),
        "has_unit": "unit" in c,
        "has_meta": "meta" in c,
        "default_unit": "credit",
    }

def _safe_json_one_line(s: str | None) -> str:
    if not s:
        return ""
    try:
        return json.dumps(json.loads(s), ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return s

def _default_start() -> date:
    # timezone-aware to avoid deprecation warnings
    return (datetime.now(timezone.utc) - timedelta(days=30)).date()

# ---------------- Filters ----------------
c1, c2, c3 = st.columns([2, 2, 2])
with c1:
    start_d = st.date_input("From", value=_default_start(), format="YYYY-MM-DD")
with c2:
    end_d = st.date_input("To", value=date.today(), format="YYYY-MM-DD")
with c3:
    limit = int(st.selectbox("Show most recent", [200, 500, 1000, 5000], index=1))

# ---------------- Queries ----------------
with get_conn() as conn:
    sch = _schema(conn)
    amt_col, dt_col = sch["amount_col"], sch["date_col"]
    if not amt_col or not dt_col:
        st.error("Rewards table is missing required columns. Run migrations and try again.")
        st.stop()

    # 1) Per-dataset totals for current owner
    per_ds = conn.execute(
        f"""
        SELECT
            r.dataset_id,
            d.name AS dataset_name,
            SUM(r.{amt_col}) AS total_amount,
            COUNT(*) AS events,
            MIN(r.{dt_col}) AS first_at,
            MAX(r.{dt_col}) AS last_at
        FROM rewards r
        JOIN datasets d ON d.id = r.dataset_id
        WHERE r.owner_id = ?
          AND DATE(r.{dt_col}) >= DATE(?)
          AND DATE(r.{dt_col}) <= DATE(?)
        GROUP BY r.dataset_id, d.name
        ORDER BY total_amount DESC
        """,
        (uid, start_d.isoformat(), end_d.isoformat()),
    ).fetchall()

    # 2) Per-org breakdown (for drilldown)
    per_org = conn.execute(
        f"""
        SELECT
            r.dataset_id,
            u.name AS org_name,
            SUM(r.{amt_col}) AS total_amount,
            COUNT(*) AS events
        FROM rewards r
        JOIN users u ON u.id = r.org_id
        WHERE r.owner_id = ?
          AND DATE(r.{dt_col}) >= DATE(?)
          AND DATE(r.{dt_col}) <= DATE(?)
        GROUP BY r.dataset_id, u.name
        ORDER BY r.dataset_id, total_amount DESC
        """,
        (uid, start_d.isoformat(), end_d.isoformat()),
    ).fetchall()

    # 3) Recent reward events (schema-adaptive meta/unit handling)
    unit_expr = "r.unit" if sch["has_unit"] else f"'{sch['default_unit']}'"
    meta_expr = "r.meta" if sch["has_meta"] else "NULL"
    recent = conn.execute(
        f"""
        SELECT
            r.{dt_col} AS at,
            d.name AS dataset_name,
            u.name AS org_name,
            r.{amt_col} AS amount,
            {unit_expr} AS unit,
            {meta_expr} AS meta,
            COALESCE(r.reason, '') AS reason
        FROM rewards r
        JOIN datasets d ON d.id = r.dataset_id
        JOIN users u    ON u.id = r.org_id
        WHERE r.owner_id = ?
          AND DATE(r.{dt_col}) >= DATE(?)
          AND DATE(r.{dt_col}) <= DATE(?)
        ORDER BY r.{dt_col} DESC
        LIMIT ?
        """,
        (uid, start_d.isoformat(), end_d.isoformat(), limit),
    ).fetchall()

# ---------------- DataFrames ----------------
df_ds = pd.DataFrame(per_ds, columns=["dataset_id", "dataset_name", "total", "events", "first_at", "last_at"])
df_org = pd.DataFrame(per_org, columns=["dataset_id", "org_name", "total", "events"])
df_recent = pd.DataFrame(recent, columns=["at", "dataset_name", "org_name", "amount", "unit", "meta", "reason"])

# ---------------- Top metrics ----------------
total_earned = int(df_ds["total"].sum()) if not df_ds.empty else 0
st.metric("Total credits (filtered range)", f"{total_earned:,}")

# ---------------- Per-dataset summary ----------------
st.subheader("Totals by dataset")
if df_ds.empty:
    st.info("No rewards in the selected period.")
else:
    st.dataframe(df_ds.sort_values("total", ascending=False), use_container_width=True, hide_index=True)
    # Simple bar chart (uses the default app theme colors)
    st.bar_chart(df_ds.set_index("dataset_name")["total"])

# ---------------- Per-org breakdown ----------------
st.subheader("Breakdown by organisation")
if df_org.empty:
    st.caption("No organisation breakdown to show.")
else:
    # Attach dataset names for readability
    if not df_ds.empty:
        name_map = dict(zip(df_ds["dataset_id"], df_ds["dataset_name"]))
        df_org["dataset_name"] = df_org["dataset_id"].map(name_map)
    st.dataframe(df_org[["dataset_name", "org_name", "total", "events"]], use_container_width=True, hide_index=True)

# ---------------- Recent reward events ----------------
st.subheader("Recent reward events")
if df_recent.empty:
    st.caption("No recent reward events.")
else:
    df_recent["meta"] = df_recent["meta"].map(_safe_json_one_line)
    st.dataframe(df_recent, use_container_width=True, hide_index=True)

    csv = df_recent.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download recent events CSV",
        data=csv,
        file_name=f"rewards_events_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )
