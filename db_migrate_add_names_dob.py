# db_migrate_add_names_dob.py
from db_init import init_schema
from db import get_conn

if __name__ == "__main__":
    # Ensure tables (including `users`) exist first
    init_schema()

    need = {
        "first_name": "TEXT",
        "last_name": "TEXT",
        "dob": "TEXT",  # ISO YYYY-MM-DD
    }

    with get_conn() as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
        for col, typ in need.items():
            if col not in cols:
                conn.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")
    print("✅ users table now has first_name, last_name, dob")
