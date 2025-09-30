# rewards.py
from __future__ import annotations

import json
import time
import sqlite3
from typing import Optional, Mapping, Any

from db import get_conn
from audit import log_reward_credited

NOW   = lambda: time.strftime("%Y-%m-%d %H:%M:%S")
TODAY = lambda: time.strftime("%Y-%m-%d")

# ---------- helpers --------------------------------------------------

def _cols(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}

def _owner_id_for_dataset(conn: sqlite3.Connection, dataset_id: int) -> int:
    row = conn.execute("SELECT owner_id FROM datasets WHERE id=?", (dataset_id,)).fetchone()
    if not row:
        raise FileNotFoundError("Dataset not found")
    return int(row[0])

def _has_credit_today(conn: sqlite3.Connection, *, dataset_id: int, org_id: int) -> bool:
    cols = _cols(conn, "rewards")
    # date column name differs by schema
    date_col = "at" if "at" in cols else ("created_at" if "created_at" in cols else None)
    if not date_col:
        # unknown custom schema -> don't dedup, but avoid crash
        return False
    row = conn.execute(
        f"""
        SELECT 1 FROM rewards
        WHERE dataset_id=? AND org_id=? AND DATE({date_col}) = DATE('now')
        LIMIT 1
        """,
        (dataset_id, org_id),
    ).fetchone()
    return row is not None

# ---------- write (schema-adaptive) ---------------------------------

def _insert_reward(
    conn: sqlite3.Connection,
    *,
    dataset_id: int,
    owner_id: int,
    org_id: int,
    amount: int,
    unit: str,
    reason: str,
    meta: Optional[Mapping[str, Any]] = None,
) -> None:
    """
    Inserts a reward row compatible with either schema:
    - Schema A (db_init.py):  id, dataset_id, org_id, owner_id, amount_cents, reason, created_at
    - Schema B (migration script): id, owner_id, org_id, dataset_id, amount, unit, reason, meta, at
    """
    cols = _cols(conn, "rewards")

    if "amount_cents" in cols:
        # Schema A (db_init.py)
        conn.execute(
            """
            INSERT INTO rewards(dataset_id, org_id, owner_id, amount_cents, reason, created_at)
            VALUES(?,?,?,?,?,?)
            """,
            (dataset_id, org_id, owner_id, int(amount), reason, NOW()),
        )
    else:
        # Schema B (migration)
        meta_json = json.dumps(dict(meta or {}), separators=(",", ":"))
        # ensure required columns exist
        has_meta = "meta" in cols
        has_unit = "unit" in cols
        has_at   = "at" in cols

        if has_meta and has_unit and has_at and "amount" in cols:
            conn.execute(
                """
                INSERT INTO rewards(owner_id, org_id, dataset_id, amount, unit, reason, meta, at)
                VALUES(?,?,?,?,?,?,?,?)
                """,
                (owner_id, org_id, dataset_id, int(amount), unit, reason, meta_json, NOW()),
            )
        else:
            # Fallback minimal insert (some custom schema) — try best effort
            # Prefer columns we know exist
            fields = ["dataset_id", "org_id", "owner_id"]
            values = [dataset_id, org_id, owner_id]
            if "amount" in cols:
                fields.append("amount"); values.append(int(amount))
            if "amount_cents" in cols:
                fields.append("amount_cents"); values.append(int(amount))
            if "unit" in cols:
                fields.append("unit"); values.append(unit)
            if "reason" in cols:
                fields.append("reason"); values.append(reason)
            if "meta" in cols:
                fields.append("meta"); values.append(meta_json)
            if "at" in cols:
                fields.append("at"); values.append(NOW())
            if "created_at" in cols and "at" not in cols:
                fields.append("created_at"); values.append(NOW())

            q = f"INSERT INTO rewards({', '.join(fields)}) VALUES({', '.join(['?']*len(values))})"
            conn.execute(q, tuple(values))

    # mirror to access_logs
    log_reward_credited(
        dataset_id=dataset_id,
        actor_id=owner_id,  # attribute to owner/admin for the credit event
        meta={"org_id": org_id, "amount": amount, "unit": unit, "reason": reason, **(meta or {})},
        conn=conn,
    )

# ---------- public API ----------------------------------------------

def credit_reward(
    conn: sqlite3.Connection,
    *,
    dataset_id: int,
    owner_id: int,
    org_id: int,
    amount: int = 1,
    unit: str = "credit",
    reason: Optional[str] = None,
    meta: Optional[Mapping[str, Any]] = None,
) -> None:
    _insert_reward(
        conn,
        dataset_id=dataset_id,
        owner_id=owner_id,
        org_id=org_id,
        amount=amount,
        unit=unit,
        reason=reason or "",
        meta=meta or {},
    )

def trigger_reward_on_access(
    conn: sqlite3.Connection,
    *,
    dataset_id: int,
    actor_id: Optional[int],
    actor_role: Optional[str],
    grant: Optional[dict],
    purpose: Optional[str] = None,
) -> None:
    """
    Reward policy (prototype):
      - Reward only when the accessor is an ORG.
      - One credit per (org, dataset) per calendar day.
      - Applies when access mode is 'trusted' or 'public'.
    """
    if not actor_id or (actor_role or "").lower() != "org":
        return

    mode = (grant or {}).get("mode", "")
    if mode not in ("trusted", "public"):
        return

    if _has_credit_today(conn, dataset_id=dataset_id, org_id=actor_id):
        return

    owner_id = _owner_id_for_dataset(conn, dataset_id)

    credit_reward(
        conn,
        dataset_id=dataset_id,
        owner_id=owner_id,
        org_id=actor_id,
        amount=1,                # if your schema uses amount_cents, this will just write "1"
        unit="credit",
        reason=f"org_access:{mode}",
        meta={"purpose": purpose or "download", "mode": mode},
    )
