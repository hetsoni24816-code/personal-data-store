# security.py
from typing import Tuple, Union
import bcrypt
import re

# --- Password hashing ---

def hash_password(plain: str) -> str:
    """
    Return a bcrypt hash (salt embedded) as a UTF-8 string for easy DB storage.
    """
    plain_bytes = plain.encode("utf-8") if isinstance(plain, str) else plain
    hashed: bytes = bcrypt.hashpw(plain_bytes, bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")

def verify_password(plain: str, hashed: Union[str, bytes]) -> bool:
    """
    Verify a plaintext password against a stored bcrypt hash.
    `hashed` may be TEXT from SQLite (str) or raw bytes.
    """
    plain_bytes = plain.encode("utf-8") if isinstance(plain, str) else plain
    hashed_bytes = hashed.encode("utf-8") if isinstance(hashed, str) else hashed
    try:
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except ValueError:
        return False

# --- Basic email/password validation (MVP) ---

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email or ""))

def valid_password(pw: str) -> Tuple[bool, str]:
    """
    MVP policy: ≥8 chars, includes a letter and a number.
    """
    if not pw or len(pw) < 8:
        return False, "Password must be at least 8 characters."
    if not any(c.isalpha() for c in pw) or not any(c.isdigit() for c in pw):
        return False, "Include at least one letter and one number."
    return True, ""

