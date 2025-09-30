# db_init.py
import sqlite3
import time
from typing import Iterable
from db import get_conn  # make sure db.py is in the same folder

NOW = lambda: time.strftime("%Y-%m-%d %H:%M:%S")

# -------------------------
# Helpers
# -------------------------

def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {r[1] for r in rows}  # name is at index 1

def ensure_column(conn: sqlite3.Connection, table: str, col: str, col_type: str) -> None:
    cols = table_columns(conn, table)
    if col not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};")

def exec_many(conn: sqlite3.Connection, statements: Iterable[str]) -> None:
    cur = conn.cursor()
    for s in statements:
        if s and s.strip():
            cur.execute(s)
    cur.close()

# -------------------------
# Schema (idempotent)
# -------------------------

USERS_SQL = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  role TEXT NOT NULL CHECK(role IN ('user','org','admin')),
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  verified INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
"""

DATASETS_SQL = """
CREATE TABLE IF NOT EXISTS datasets(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  mime TEXT,
  content_enc BLOB NOT NULL,
  visibility TEXT NOT NULL CHECK(visibility IN ('Private','Trusted','Public')) DEFAULT 'Private',
  version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT,
  FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE
);
"""

PERMISSIONS_SQL = """
CREATE TABLE IF NOT EXISTS permissions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dataset_id INTEGER NOT NULL,
  org_id INTEGER NOT NULL,
  allow INTEGER NOT NULL CHECK(allow IN (0,1)) DEFAULT 1,
  scope TEXT,             -- e.g. 'agg-only|no-ads|no-LLMs'
  expires_at TEXT,        -- ISO8601 or NULL
  status TEXT NOT NULL CHECK(status IN ('granted','revoked','pending')) DEFAULT 'granted',
  created_at TEXT NOT NULL,
  updated_at TEXT,
  FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
  FOREIGN KEY(org_id)     REFERENCES users(id)     ON DELETE CASCADE,
  CONSTRAINT uniq_dataset_org UNIQUE(dataset_id, org_id)
);
"""

ACCESS_LOGS_SQL = """
CREATE TABLE IF NOT EXISTS access_logs(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dataset_id INTEGER NOT NULL,
  actor_id INTEGER NOT NULL,
  actor_role TEXT NOT NULL CHECK(actor_role IN ('user','org','admin')),
  action TEXT NOT NULL CHECK(action IN (
      'upload','permissions_update','request_access','grant','revoke',
      'view_meta','download','denied','login_failed','login_succeeded',
      'reward_credited'
  )),
  meta TEXT,
  at TEXT NOT NULL,
  FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
  FOREIGN KEY(actor_id)   REFERENCES users(id)    ON DELETE CASCADE
);
"""

REWARDS_SQL = """
CREATE TABLE IF NOT EXISTS rewards(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dataset_id INTEGER NOT NULL,
  org_id INTEGER NOT NULL,
  owner_id INTEGER NOT NULL,
  amount_cents INTEGER NOT NULL CHECK(amount_cents >= 0),
  reason TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
  FOREIGN KEY(org_id)     REFERENCES users(id)    ON DELETE CASCADE,
  FOREIGN KEY(owner_id)   REFERENCES users(id)    ON DELETE CASCADE
);
"""

INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_datasets_owner      ON datasets(owner_id);",
    "CREATE INDEX IF NOT EXISTS idx_datasets_visibility ON datasets(visibility);",
    "CREATE UNIQUE INDEX IF NOT EXISTS uniq_owner_name_ver ON datasets(owner_id, name, version);",
    "CREATE INDEX IF NOT EXISTS idx_permissions_ds ON permissions(dataset_id);",
    "CREATE INDEX IF NOT EXISTS idx_permissions_org ON permissions(org_id);",
    "CREATE INDEX IF NOT EXISTS idx_logs_ds_time   ON access_logs(dataset_id, at);",
    "CREATE INDEX IF NOT EXISTS idx_rewards_owner  ON rewards(owner_id);",
]

VIEW_SQL = """
CREATE VIEW IF NOT EXISTS v_latest_datasets AS
  SELECT d.*
  FROM datasets d
  JOIN (
    SELECT owner_id, name, MAX(version) AS max_ver
    FROM datasets
    GROUP BY owner_id, name
  ) m
  ON d.owner_id = m.owner_id AND d.name = m.name AND d.version = m.max_ver;
"""

TRIGGERS_SQL = [
    """
    CREATE TRIGGER IF NOT EXISTS trg_datasets_update AFTER UPDATE ON datasets
    BEGIN
      UPDATE datasets SET updated_at = DATETIME('now') WHERE id = NEW.id;
    END;
    """,
    """
    CREATE TRIGGER IF NOT EXISTS trg_permissions_update AFTER UPDATE ON permissions
    BEGIN
      UPDATE permissions SET updated_at = DATETIME('now') WHERE id = NEW.id;
    END;
    """,
]

# -------------------------
# Initialization
# -------------------------

def init_schema() -> None:
    with get_conn() as conn:
        # Base tables
        exec_many(conn, [USERS_SQL, DATASETS_SQL, PERMISSIONS_SQL, ACCESS_LOGS_SQL, REWARDS_SQL])
        # Backfill columns for users (if table existed before)
        ensure_column(conn, "users", "first_name", "TEXT")
        ensure_column(conn, "users", "last_name",  "TEXT")
        ensure_column(conn, "users", "dob",        "TEXT")  # store as YYYY-MM-DD
        ensure_column(conn, "users", "last_login", "TEXT")

        # Indexes, view, triggers
        exec_many(conn, INDEXES_SQL + [VIEW_SQL] + TRIGGERS_SQL)

def seed_demo() -> None:
    """Optional: create one demo user and one demo org (password = 'Password123')."""
    from security import hash_password
    with get_conn() as conn:
        # user
        conn.execute(
            """INSERT OR IGNORE INTO users(id, role, name, first_name, last_name, dob,
                                           email, password_hash, verified, created_at)
               VALUES(1,'user','Alice User','Alice','User','2000-01-01',
                      'alice@example.com', ?, 1, ?)""",
            (hash_password("Password123"), NOW()),
        )
        # org
        conn.execute(
            """INSERT OR IGNORE INTO users(id, role, name, first_name, last_name, dob,
                                           email, password_hash, verified, created_at)
               VALUES(2,'org','Acme Research','Acme','Research','2000-01-01',
                      'org@example.com', ?, 1, ?)""",
            (hash_password("Password123"), NOW()),
        )

def sanity_check() -> None:
    with get_conn() as conn:
        objs = conn.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') ORDER BY type, name;").fetchall()
        print("Schema objects:")
        for name, typ in objs:
            print(f" - {typ:<5} {name}")
        # Quick users columns print
        cols = conn.execute("PRAGMA table_info(users);").fetchall()
        print("\nusers columns:")
        for c in cols:
            print(f" - {c[1]} {c[2]}")
        print("\n✅ DB ready.")

if __name__ == "__main__":
    init_schema()
    # seed_demo()   # optional: uncomment to create sample users
    sanity_check()  # <-- prints schema and “✅ DB ready.”
