"""
audit.py — Centralized audit logging for access_logs table.

Features
--------
- log_event(...) inserts into access_logs with validated action & role
- Convenience wrappers for common actions:
    log_upload, log_permissions_update, log_request_access,
    log_grant, log_revoke, log_download, log_denied,
    log_login_succeeded, log_login_failed, log_reward_credited
"""

import json
import time
import sqlite3
from typing import Optional, Mapping, Any

from db import get_conn

NOW = lambda: time.strftime("%Y-%m-%d %H:%M:%S")

# -------------------------------------------------------------------
# Allowed values for validation
# -------------------------------------------------------------------
ALLOWED_ACTIONS = {
    "upload",
    "permissions_update",
    "request_access",
    "grant",
    "revoke",
    "view_meta",
    "download",
    "denied",
    "login_failed",
    "login_succeeded",
    "reward_credited",
}

ALLOWED_ROLES = {"user", "org", "admin"}

# -------------------------------------------------------------------
# Core function
# -------------------------------------------------------------------
def log_event(
    dataset_id: int,
    actor_id: int,
    actor_role: str,
    action: str,
    meta: Optional[Mapping[str, Any]] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    """
    Insert a row into access_logs.
    If `conn` is provided, reuse it (avoids 'database is locked').
    """
    action = (action or "").strip()
    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"Invalid action '{action}'. Allowed: {sorted(ALLOWED_ACTIONS)}")

    actor_role = (actor_role or "").strip()
    if actor_role not in ALLOWED_ROLES:
        raise ValueError(f"Invalid actor_role '{actor_role}'. Allowed: {sorted(ALLOWED_ROLES)}")

    payload = json.dumps(dict(meta or {}), separators=(",", ":"))
    sql = """
        INSERT INTO access_logs(dataset_id, actor_id, actor_role, action, meta, at)
        VALUES(?,?,?,?,?,?)
    """
    params = (dataset_id, actor_id, actor_role, action, payload, NOW())

    if conn is not None:
        conn.execute(sql, params)
    else:
        with get_conn() as c:
            c.execute(sql, params)

# -------------------------------------------------------------------
# Convenience wrappers
# -------------------------------------------------------------------
def log_upload(dataset_id: int, actor_id: int, meta: Optional[Mapping[str, Any]] = None,
               conn: Optional[sqlite3.Connection] = None) -> None:
    log_event(dataset_id, actor_id, "user", "upload", meta=meta, conn=conn)

def log_permissions_update(dataset_id: int, actor_id: int, meta: Mapping[str, Any],
                           conn: Optional[sqlite3.Connection] = None) -> None:
    log_event(dataset_id, actor_id, "user", "permissions_update", meta=meta, conn=conn)

def log_request_access(dataset_id: int, actor_id: int, meta: Mapping[str, Any],
                       conn: Optional[sqlite3.Connection] = None) -> None:
    log_event(dataset_id, actor_id, "org", "request_access", meta=meta, conn=conn)

def log_grant(dataset_id: int, actor_id: int, meta: Mapping[str, Any],
              conn: Optional[sqlite3.Connection] = None) -> None:
    log_event(dataset_id, actor_id, "user", "grant", meta=meta, conn=conn)

def log_revoke(dataset_id: int, actor_id: int, meta: Mapping[str, Any],
               conn: Optional[sqlite3.Connection] = None) -> None:
    log_event(dataset_id, actor_id, "user", "revoke", meta=meta, conn=conn)

def log_download(dataset_id: int, actor_id: int, role: str = "org",
                 meta: Optional[Mapping[str, Any]] = None,
                 conn: Optional[sqlite3.Connection] = None) -> None:
    if role not in ALLOWED_ROLES:
        role = "org"
    log_event(dataset_id, actor_id, role, "download", meta=meta, conn=conn)

def log_denied(dataset_id: int, actor_id: int, role: str = "org",
               meta: Optional[Mapping[str, Any]] = None,
               conn: Optional[sqlite3.Connection] = None) -> None:
    if role not in ALLOWED_ROLES:
        role = "org"
    log_event(dataset_id, actor_id, role, "denied", meta=meta, conn=conn)

def log_login_succeeded(actor_id: int, meta: Optional[Mapping[str, Any]] = None) -> None:
    log_event(0, actor_id, "user", "login_succeeded", meta=meta)

def log_login_failed(actor_id: int, meta: Optional[Mapping[str, Any]] = None) -> None:
    log_event(0, actor_id, "user", "login_failed", meta=meta)

def log_reward_credited(dataset_id: int, actor_id: int, meta: Mapping[str, Any],
                        conn: Optional[sqlite3.Connection] = None) -> None:
    log_event(dataset_id, actor_id, "admin", "reward_credited", meta=meta, conn=conn)
