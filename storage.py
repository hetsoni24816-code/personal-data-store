# storage.py
"""
Encrypted dataset storage with versioning, permissions, rewards, and auditing.

Public API
----------
save_dataset(owner_id, file_name, mime, raw_bytes, description="", visibility="Private")
    -> (dataset_id, version)

list_my_latest(owner_id: int, limit: int = 25)
    -> List[(id, name, version, visibility, created_at)]

list_versions(owner_id: int, name: str)
    -> List[(id, version, visibility, created_at)]

change_visibility(owner_id: int, dataset_id: int, new_visibility: str) -> bool

get_dataset_bytes(dataset_id: int) -> bytes
    Raw decrypt without permission checks (owner/admin utilities)

get_dataset_for_download(dataset_id: int, actor_id: int|None, actor_role: str|None, purpose="download")
    -> (bytes, filename, mime)
    Permission-checked & audited (download / denied) and triggers rewards.

get_dataset_bytes_secure(dataset_id: int, actor_id: int|None, actor_role: str|None, purpose="download")
    -> bytes  (thin wrapper around get_dataset_for_download)
"""

from __future__ import annotations

import time
from typing import List, Tuple, Optional

from db import get_conn
from filesec import encrypt_bytes, decrypt_bytes
from access import can_access
from rewards import trigger_reward_on_access
from audit import (
    log_upload,
    log_permissions_update,
    log_download,
    log_denied,
)

# ---------------------- constants / utils ----------------------

NOW = lambda: time.strftime("%Y-%m-%d %H:%M:%S")

ALLOWED_VIS = {"Private", "Trusted", "Public"}
DEFAULT_MIME = "application/octet-stream"


def _bytes_from_blob(blob) -> bytes:
    """Normalize SQLite BLOB (bytes or memoryview) to bytes."""
    if isinstance(blob, memoryview):
        return blob.tobytes()
    return blob


def _next_version(conn, owner_id: int, name: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(version), 0) FROM datasets WHERE owner_id=? AND name=?",
        (owner_id, name),
    ).fetchone()
    return int(row[0]) + 1


# ---------------------- write paths ----------------------

def save_dataset(
    *,
    owner_id: int,
    file_name: str,
    mime: Optional[str],
    raw_bytes: bytes,
    description: str = "",
    visibility: str = "Private",
) -> Tuple[int, int]:
    """
    Encrypt and store a new version of (owner_id, file_name).
    Returns (dataset_id, version). Also logs 'upload'.
    """
    if not file_name:
        raise ValueError("file_name is required")

    vis = (visibility or "Private").strip().title()
    if vis not in ALLOWED_VIS:
        raise ValueError(f"Invalid visibility '{visibility}'. Allowed: {sorted(ALLOWED_VIS)}")

    m = (mime or DEFAULT_MIME).strip() or DEFAULT_MIME
    desc = (description or "").strip()

    # Encrypt payload before write
    ciphertext = encrypt_bytes(raw_bytes)

    with get_conn() as conn:
        ver = _next_version(conn, owner_id, file_name)
        cur = conn.execute(
            """
            INSERT INTO datasets(owner_id, name, description, mime, content_enc, visibility, version, created_at)
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (owner_id, file_name, desc, m, ciphertext, vis, ver, NOW()),
        )
        ds_id = int(cur.lastrowid)

        # Audit: upload
        log_upload(
            dataset_id=ds_id,
            actor_id=owner_id,
            meta={"name": file_name, "mime": m, "size": len(raw_bytes), "version": ver, "visibility": vis},
            conn=conn,
        )

        return ds_id, ver


# ---------------------- listings ----------------------

def list_my_latest(owner_id: int, limit: int = 25) -> List[Tuple[int, str, int, str, str]]:
    """
    Latest version of each filename for the owner.
    Returns list of (id, name, version, visibility, created_at), newest first.
    """
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT d.id, d.name, d.version, d.visibility, d.created_at
            FROM datasets d
            WHERE d.owner_id = ?
              AND d.version = (
                  SELECT MAX(d2.version)
                  FROM datasets d2
                  WHERE d2.owner_id = d.owner_id AND d2.name = d.name
              )
            ORDER BY d.created_at DESC, d.id DESC
            LIMIT ?
            """,
            (owner_id, limit),
        ).fetchall()
    return rows


def list_versions(owner_id: int, name: str) -> List[Tuple[int, int, str, str]]:
    """
    Version history for a given filename (owned by owner_id).
    Returns (id, version, visibility, created_at) newest first.
    """
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, version, visibility, created_at
            FROM datasets
            WHERE owner_id=? AND name=?
            ORDER BY version DESC, id DESC
            """,
            (owner_id, name),
        ).fetchall()
    return rows


# ---------------------- updates ----------------------

def change_visibility(*, owner_id: int, dataset_id: int, new_visibility: str) -> bool:
    """
    Change visibility for a dataset IF caller is owner.
    Returns True if updated; False if not owner / not found / no change.
    Audits as 'permissions_update' (op=set_visibility).
    """
    vis = (new_visibility or "").strip().title()
    if vis not in ALLOWED_VIS:
        raise ValueError(f"Invalid visibility '{new_visibility}'. Allowed: {sorted(ALLOWED_VIS)}")

    with get_conn() as conn:
        row = conn.execute(
            "SELECT owner_id, visibility FROM datasets WHERE id=?",
            (dataset_id,),
        ).fetchone()
        if not row:
            return False
        owner_row, old_vis = row
        if owner_row != owner_id:
            return False
        if old_vis == vis:
            return True  # no-op

        conn.execute(
            "UPDATE datasets SET visibility=?, updated_at=? WHERE id=?",
            (vis, NOW(), dataset_id),
        )
        log_permissions_update(
            dataset_id=dataset_id,
            actor_id=owner_id,
            meta={"op": "set_visibility", "old": old_vis, "new": vis},
            conn=conn,
        )
        return True


# ---------------------- reads (unsafe & safe) ----------------------

def get_dataset_bytes(dataset_id: int) -> bytes:
    """
    Raw decrypt WITHOUT permission checks.
    Prefer get_dataset_for_download(...) for user-facing access.
    """
    with get_conn() as conn:
        row = conn.execute(
            "SELECT content_enc FROM datasets WHERE id=?",
            (dataset_id,),
        ).fetchone()
        if not row:
            raise FileNotFoundError("Dataset not found")
        enc = _bytes_from_blob(row[0])
    return decrypt_bytes(enc)


def get_dataset_for_download(
    dataset_id: int,
    actor_id: Optional[int],
    actor_role: Optional[str],
    purpose: str = "download",
):
    """
    Secure fetch with audit and rewards:
    - checks permission (Private/Trusted/Public, owner/admin overrides)
    - if denied: logs 'denied' and raises PermissionError
    - if allowed: decrypts bytes, logs 'download',
      triggers reward for org access, and returns (bytes, filename, mime)
    """
    with get_conn() as conn:
        allowed, reason, grant = can_access(
            dataset_id=dataset_id,
            actor_id=actor_id,
            actor_role=actor_role,
            purpose=purpose,
            conn=conn,
        )

        if not allowed:
            log_denied(
                dataset_id=dataset_id,
                actor_id=actor_id or 0,
                role=actor_role or "user",
                meta={"reason": reason, "purpose": purpose},
                conn=conn,
            )
            raise PermissionError(f"Access denied: {reason}")

        row = conn.execute(
            "SELECT name, mime, content_enc FROM datasets WHERE id=?",
            (dataset_id,),
        ).fetchone()
        if not row:
            raise FileNotFoundError("Dataset not found")

        name, mime, enc = row[0], (row[1] or DEFAULT_MIME), _bytes_from_blob(row[2])
        data = decrypt_bytes(enc)

        # Audit allowed download
        log_download(
            dataset_id=dataset_id,
            actor_id=actor_id or 0,
            role=actor_role or "user",
            meta={"purpose": purpose, **(grant or {})},
            conn=conn,
        )

        # Reward on org access (same transaction/connection)
        trigger_reward_on_access(
            conn,
            dataset_id=dataset_id,
            actor_id=actor_id,
            actor_role=actor_role,
            grant=grant,
            purpose=purpose,
        )

        return data, name, mime


def get_dataset_bytes_secure(
    dataset_id: int,
    actor_id: Optional[int],
    actor_role: Optional[str],
    purpose: str = "download",
) -> bytes:
    """Convenience wrapper when only bytes are needed."""
    data, _, _ = get_dataset_for_download(dataset_id, actor_id, actor_role, purpose)
    return data
