# filesec.py
import os
from cryptography.fernet import Fernet  # pip install cryptography

_KEY_PATH = "pds_files.key"
_cipher = None

def _load_key() -> bytes:
    if not os.path.exists(_KEY_PATH):
        with open(_KEY_PATH, "wb") as f:
            f.write(Fernet.generate_key())
    return open(_KEY_PATH, "rb").read()

def cipher() -> Fernet:
    global _cipher
    if _cipher is None:
        _cipher = Fernet(_load_key())
    return _cipher

def encrypt_bytes(b: bytes) -> bytes:
    return cipher().encrypt(b)

def decrypt_bytes(b: bytes) -> bytes:
    return cipher().decrypt(b)
