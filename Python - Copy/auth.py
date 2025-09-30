# auth.py
import time, sqlite3
from typing import Tuple, Optional, Dict, Any
from db import get_conn
from security import hash_password, verify_password, valid_email, valid_password

NOW = lambda: time.strftime("%Y-%m-%d %H:%M:%S")

def create_user(
    first_name: str,
    last_name: str,
    dob_iso: str,            # "YYYY-MM-DD"
    email: str,
    password: str,
    role: str = "user",
    auto_verify: bool = True,
) -> Tuple[bool, str]:
    """
    Registers a user with first/last name and DOB. Returns (ok, message).
    """
    email = (email or "").strip().lower()
    first_name = (first_name or "").strip()
    last_name  = (last_name  or "").strip()

    if not first_name or not last_name:
        return False, "Please enter your first and last name."
    if not dob_iso:
        return False, "Please select your date of birth."
    if role not in ("user", "org", "admin"):
        return False, "Invalid role."
    if not valid_email(email):
        return False, "Invalid email format."

    ok, msg = valid_password(password)
    if not ok:
        return False, msg

    full_name = f"{first_name} {last_name}".strip()
    pw_hash = hash_password(password)

    try:
        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO users(role, name, first_name, last_name, dob,
                                  email, password_hash, verified, created_at)
                VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (role, full_name, first_name, last_name, dob_iso,
                 email, pw_hash, 1 if auto_verify else 0, NOW()),
            )
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."

def authenticate(email: str, password: str) -> Optional[Dict[str, Any]]:
    email = (email or "").strip().lower()
    with get_conn() as conn:
        row = conn.execute(
            """SELECT id, role, name, email, password_hash, verified
               FROM users WHERE email=?""",
            (email,),
        ).fetchone()
    if not row:
        return None
    uid, role, name, email, pw_hash, verified = row
    if not verify_password(password, pw_hash):
        return None
    if not verified:
        return None
    with get_conn() as conn:
        conn.execute("UPDATE users SET last_login=? WHERE id=?", (NOW(), uid))
    return {"id": uid, "role": role, "name": name, "email": email, "verified": verified}
