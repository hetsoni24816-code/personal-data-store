# tools/make_admin.py
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import get_conn

email = input("Enter the email of the user to promote to admin: ").strip().lower()

with get_conn() as conn:
    cur = conn.execute("UPDATE users SET role='admin' WHERE email=?", (email,))
    if cur.rowcount:
        print(f"{email} is now an admin.")
    else:
        print(f"No user found with email {email}.")
