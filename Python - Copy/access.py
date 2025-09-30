# access.py
"""
Central permission check for dataset reads.

can_access(dataset_id, actor_id, actor_role, purpose=None, conn=None)
 -> (allowed: bool, reason: str, grant: dict)

Policies
- Owner (and admin) can always access.
- Public  : everyone can access (even if actor_id=None).
- Private : only owner (and admin).
- Trusted : only orgs that have an active grant (permissions.allow=1 AND status='granted'
            AND (expires_at is NULL or >= today)). Org must be verified=1.
- Returns 'grant' details with mode, scope, expires_at to drive UI/logging.

Use assert_can_access(...) to raise an error and optionally log.

All DB I/O is within a single connection (pass conn to reuse transactions).
"""

from __future__ import annotations
import time
from typing import Optional, Tuple, Dict, Any
import sqlite3

from db import get_conn
from audit import log_event

TODAY = lambda: time.strftime("%Y-%m-%d")
NOW   = lambda: time.strftime("%Y-%m-%d %H:%M:%S")


def _fetch_dataset(conn: sqlite3.Connection, dataset_id: int):
    row = conn.execute(
        "SELECT id, owner_id, visibility, name FROM datasets WHERE id=?",
        (dataset_id,),
    ).fetchone()
    return row  # (id, owner_id, visibility, name) or None


def _fetch_user(conn: sqlite3.Connection, user_id: int):
    if user_id is None:
        return None
    return conn.execute(
        "SELECT id, role, verified, name FROM users WHERE id=?",
        (user_id,),
    ).fetchone()  # (id, role, verified, name)


def _fetch_grant(conn: sqlite3.Connection, dataset_id: int, org_id: int):
    return conn.execute(
        """
        SELECT allow, status, scope, expires_at
        FROM permissions
        WHERE dataset_id=? AND org_id=?
        """,
        (dataset_id, org_id),
    ).fetchone()  # (allow, status, scope, expires_at) or None


def can_access(
    *,
    dataset_id: int,
    actor_id: Optional[int],
    actor_role: Optional[str],
    purpose: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Returns (allowed, reason, grant_info).

    reason is one of:
      'ok', 'not_found', 'private', 'trusted_only', 'not_trusted',
      'expired', 'unverified_org', 'forbidden'
    grant_info contains:
      mode: 'owner'|'admin'|'public'|'trusted'
      scope: Optional[str]
      expires_at: Optional[str]
    """
    close_conn = False
    if conn is None:
        conn = get_conn()
        close_conn = True

    try:
        ds = _fetch_dataset(conn, dataset_id)
        if not ds:
            return False, "not_found", {}

        _id, owner_id, visibility, name = ds

        # Owner & admin override
        if actor_id is not None:
            u = _fetch_user(conn, actor_id)
            if u:
                _uid, role, verified, uname = u
                if actor_id == owner_id:
                    return True, "ok", {"mode": "owner", "scope": None, "expires_at": None}
                if role == "admin":
                    return True, "ok", {"mode": "admin", "scope": None, "expires_at": None}
            else:
                # Unknown user id
                return False, "forbidden", {}

        # Public open access
        if visibility == "Public":
            return True, "ok", {"mode": "public", "scope": None, "expires_at": None}

        # Private -> only owner/admin (already handled)
        if visibility == "Private":
            return False, "private", {}

        # Trusted -> check org grant
        if visibility == "Trusted":
            # must be an org and verified
            if not actor_id or (actor_role != "org"):
                return False, "trusted_only", {}
            u = _fetch_user(conn, actor_id)
            if not u or u[2] != 1:  # verified flag
                return False, "unverified_org", {}
            grant = _fetch_grant(conn, dataset_id, actor_id)
            if not grant:
                return False, "not_trusted", {}
            allow, status, scope, expires_at = grant
            if not allow or status != "granted":
                return False, "not_trusted", {}
            if expires_at and expires_at < TODAY():
                return False, "expired", {"mode": "trusted", "scope": scope, "expires_at": expires_at}
            return True, "ok", {"mode": "trusted", "scope": scope, "expires_at": expires_at}

        # Unknown visibility
        return False, "forbidden", {}

    finally:
        if close_conn:
            conn.close()


def assert_can_access(
    *,
    dataset_id: int,
    actor_id: Optional[int],
    actor_role: Optional[str],
    purpose: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    log: bool = True,
) -> Dict[str, Any]:
    """
    Raises PermissionError on denial.
    Logs `data_access_denied` or `data_access_allowed` when log=True.
    Returns grant_info on success.
    """
    allowed, reason, grant = can_access(
        dataset_id=dataset_id, actor_id=actor_id, actor_role=actor_role, purpose=purpose, conn=conn
    )
    if log:
        # Use the same connection when provided to avoid SQLite write contention
        log_event(
            dataset_id=dataset_id,
            actor_id=actor_id or 0,
            actor_role=actor_role or "-",
            action="data_access_allowed" if allowed else "data_access_denied",
            meta={"reason": reason, "purpose": purpose, **grant},
            conn=conn,
        )
    if not allowed:
        raise PermissionError(f"Access denied: {reason}")
    return grant
