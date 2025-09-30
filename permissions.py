# permissions.py
"""
Permission storage, requests, and updates.

Features:
- Directory & reads:
    list_org_directory(), list_trusted_org_ids(dataset_id), list_trusted_orgs(dataset_id)
    list_my_requests(org_id), list_pending_requests_for_owner(owner_id)
- Single changes:
    grant_access(...), revoke_access(...), update_permission_details(...)
- Bulk changes:
    set_trusted_orgs(...): add/remove trusted orgs in one transaction
- Org request / owner approval:
    request_access(...), approve_request(...), deny_request(...)

All writes use one transaction (get_conn()) and log via audit.log_event with the
same connection to prevent SQLite write-contention.
"""

from __future__ import annotations

import time
import sqlite3
from typing import List, Tuple, Optional, Dict, Any

from db import get_conn
from audit import log_event

NOW = lambda: time.strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------
# Helpers (internal)
# ---------------------------------------------------------------------

def _sanitize_scope(scope: Optional[str]) -> Optional[str]:
    s = (scope or "").strip()
    return s or None

def _upsert_permission(
    conn: sqlite3.Connection,
    dataset_id: int,
    org_id: int,
    *,
    allow: int,
    status: str,
    scope: Optional[str] = None,
    expires_at: Optional[str] = None,
) -> None:
    """Create-or-update a permissions row atomically."""
    conn.execute(
        """
        INSERT OR IGNORE INTO permissions(dataset_id, org_id, allow, scope, expires_at, status, created_at)
        VALUES(?,?,?,?,?,?,?)
        """,
        (dataset_id, org_id, int(allow), scope, expires_at, status, NOW()),
    )
    conn.execute(
        """
        UPDATE permissions
        SET allow=?, status=?, scope=?, expires_at=?, updated_at=?
        WHERE dataset_id=? AND org_id=?
        """,
        (int(allow), status, scope, expires_at, NOW(), dataset_id, org_id),
    )


# ---------------------------------------------------------------------
# Directory & read APIs
# ---------------------------------------------------------------------

def list_org_directory() -> List[Tuple[int, str, str]]:
    """All verified organisations: (id, name, email)."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, name, email FROM users WHERE role='org' AND verified=1 ORDER BY name COLLATE NOCASE"
        ).fetchall()

def list_trusted_org_ids(dataset_id: int) -> List[int]:
    """Org IDs that currently have access (allow=1 & status='granted')."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT org_id FROM permissions WHERE dataset_id=? AND allow=1 AND status='granted'",
            (dataset_id,),
        ).fetchall()
    return [r[0] for r in rows]

def list_trusted_orgs(dataset_id: int) -> List[Tuple[int, str, str, int, str, Optional[str], Optional[str]]]:
    """
    Detailed trusted orgs for dataset_id.
    Returns: (org_id, name, email, allow, status, scope, expires_at)
    """
    with get_conn() as conn:
        q = """
        SELECT u.id, u.name, u.email, p.allow, p.status, p.scope, p.expires_at
        FROM permissions p
        JOIN users u ON u.id = p.org_id
        WHERE p.dataset_id=?
        ORDER BY u.name COLLATE NOCASE
        """
        return conn.execute(q, (dataset_id,)).fetchall()


# ---------------------------------------------------------------------
# Single changes (grant / revoke / update details)
# ---------------------------------------------------------------------

def grant_access(
    *,
    dataset_id: int,
    owner_id: int,
    org_id: int,
    scope: Optional[str] = None,
    expires_at: Optional[str] = None,
) -> None:
    """Grant access to one org; logs 'grant' + 'permissions_update'."""
    scope = _sanitize_scope(scope)
    with get_conn() as conn:
        _upsert_permission(conn, dataset_id, org_id, allow=1, status="granted",
                           scope=scope, expires_at=expires_at)
        log_event(dataset_id, owner_id, "user", "grant",
                  meta={"org_id": org_id, "scope": scope, "expires_at": expires_at}, conn=conn)
        log_event(dataset_id, owner_id, "user", "permissions_update",
                  meta={"op": "grant", "org_id": org_id}, conn=conn)

def revoke_access(
    *,
    dataset_id: int,
    owner_id: int,
    org_id: int,
) -> None:
    """Revoke access from one org; logs 'revoke' + 'permissions_update'."""
    with get_conn() as conn:
        _upsert_permission(conn, dataset_id, org_id, allow=0, status="revoked")
        log_event(dataset_id, owner_id, "user", "revoke",
                  meta={"org_id": org_id}, conn=conn)
        log_event(dataset_id, owner_id, "user", "permissions_update",
                  meta={"op": "revoke", "org_id": org_id}, conn=conn)

def update_permission_details(
    *,
    dataset_id: int,
    owner_id: int,
    org_id: int,
    scope: Optional[str],
    expires_at: Optional[str],
) -> None:
    """Update scope/expiry for an org; logs 'permissions_update'."""
    scope = _sanitize_scope(scope)
    with get_conn() as conn:
        _upsert_permission(conn, dataset_id, org_id, allow=1, status="granted",
                           scope=scope, expires_at=expires_at)
        log_event(
            dataset_id, owner_id, "user", "permissions_update",
            meta={"op": "update_details", "org_id": org_id, "scope": scope, "expires_at": expires_at},
            conn=conn,
        )


# ---------------------------------------------------------------------
# Bulk changes (multiselect)
# ---------------------------------------------------------------------

def set_trusted_orgs(
    *,
    dataset_id: int,
    owner_id: int,
    new_org_ids: List[int],
    default_scope: Optional[str] = None,
    default_expires_at: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Diff current vs desired trusted orgs and apply in one transaction.
    Logs one 'permissions_update' per add/remove; also logs 'grant'/'revoke'.
    Returns: {"added": [...], "removed": [...]}
    """
    default_scope = _sanitize_scope(default_scope)

    with get_conn() as conn:
        current = set(oid for (oid,) in conn.execute(
            "SELECT org_id FROM permissions WHERE dataset_id=? AND allow=1 AND status='granted'",
            (dataset_id,),
        ).fetchall())
        desired = set(new_org_ids)

        added = sorted(list(desired - current))
        removed = sorted(list(current - desired))

        for org_id in added:
            _upsert_permission(conn, dataset_id, org_id, allow=1, status="granted",
                               scope=default_scope, expires_at=default_expires_at)
            log_event(dataset_id, owner_id, "user", "grant",
                      meta={"org_id": org_id, "scope": default_scope, "expires_at": default_expires_at}, conn=conn)
            log_event(dataset_id, owner_id, "user", "permissions_update",
                      meta={"op": "grant", "org_id": org_id}, conn=conn)

        for org_id in removed:
            _upsert_permission(conn, dataset_id, org_id, allow=0, status="revoked")
            log_event(dataset_id, owner_id, "user", "revoke",
                      meta={"org_id": org_id}, conn=conn)
            log_event(dataset_id, owner_id, "user", "permissions_update",
                      meta={"op": "revoke", "org_id": org_id}, conn=conn)

        return {"added": added, "removed": removed}


# ---------------------------------------------------------------------
# Org requests & owner approvals
# ---------------------------------------------------------------------

def request_access(*, dataset_id: int, org_id: int, message: Optional[str] = None) -> None:
    """
    Org requests access to a dataset: mark row as pending (allow=0, status='pending').
    Logs 'request_access' with optional message.
    """
    msg = (message or "").strip()
    with get_conn() as conn:
        _upsert_permission(conn, dataset_id, org_id, allow=0, status="pending")
        log_event(
            dataset_id=dataset_id,
            actor_id=org_id,
            actor_role="org",
            action="request_access",
            meta={"message": msg},
            conn=conn,
        )

def list_my_requests(org_id: int) -> List[Tuple[int, str, int, str, str]]:
    """
    Org's outgoing requests.
    Returns: (dataset_id, dataset_name, owner_id, status, last_ts)
    """
    with get_conn() as conn:
        q = """
        SELECT p.dataset_id, d.name, d.owner_id, p.status,
               COALESCE(p.updated_at, p.created_at) AS ts
        FROM permissions p
        JOIN datasets d ON d.id = p.dataset_id
        WHERE p.org_id=? AND p.status IN ('pending','granted','revoked')
        ORDER BY ts DESC
        """
        return conn.execute(q, (org_id,)).fetchall()

def list_pending_requests_for_owner(owner_id: int) -> List[Tuple[int, str, int, str, str]]:
    """
    Owner's incoming pending requests.
    Returns: (dataset_id, dataset_name, org_id, org_name, requested_at)
    """
    with get_conn() as conn:
        q = """
        SELECT p.dataset_id, d.name, u.id AS org_id, u.name AS org_name, p.created_at
        FROM permissions p
        JOIN datasets d ON d.id = p.dataset_id
        JOIN users u     ON u.id = p.org_id
        WHERE d.owner_id=? AND p.status='pending'
        ORDER BY p.created_at DESC
        """
        return conn.execute(q, (owner_id,)).fetchall()

def approve_request(
    *,
    dataset_id: int,
    owner_id: int,
    org_id: int,
    scope: Optional[str] = None,
    expires_at: Optional[str] = None,
) -> None:
    """
    Owner approves a pending request -> granted/allow=1.
    Logs 'grant' and 'permissions_update'.
    """
    scope = _sanitize_scope(scope)
    with get_conn() as conn:
        _upsert_permission(conn, dataset_id, org_id, allow=1, status="granted",
                           scope=scope, expires_at=expires_at)
        log_event(dataset_id, owner_id, "user", "grant",
                  meta={"org_id": org_id, "scope": scope, "expires_at": expires_at}, conn=conn)
        log_event(dataset_id, owner_id, "user", "permissions_update",
                  meta={"op": "approve_request", "org_id": org_id}, conn=conn)

def deny_request(
    *,
    dataset_id: int,
    owner_id: int,
    org_id: int,
    reason: Optional[str] = None,
) -> None:
    """
    Owner denies a pending request -> revoked/allow=0.
    Logs 'denied' and 'permissions_update'.
    """
    reason = (reason or "").strip()
    with get_conn() as conn:
        _upsert_permission(conn, dataset_id, org_id, allow=0, status="revoked")
        log_event(dataset_id, owner_id, "user", "denied",
                  meta={"org_id": org_id, "reason": reason}, conn=conn)
        log_event(dataset_id, owner_id, "user", "permissions_update",
                  meta={"op": "deny_request", "org_id": org_id}, conn=conn)
