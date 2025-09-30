# db_migrate_add_rewards.py
from db import get_conn

DDL = """
CREATE TABLE IF NOT EXISTS rewards(
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id    INTEGER NOT NULL,
  org_id      INTEGER NOT NULL,
  dataset_id  INTEGER NOT NULL,
  amount      INTEGER NOT NULL DEFAULT 1,       -- simple points/credits
  unit        TEXT    NOT NULL DEFAULT 'credit',
  reason      TEXT,
  meta        TEXT,
  at          TEXT    NOT NULL                  -- ISO timestamp
);
CREATE INDEX IF NOT EXISTS idx_rewards_owner   ON rewards(owner_id, at);
CREATE INDEX IF NOT EXISTS idx_rewards_org     ON rewards(org_id, at);
CREATE INDEX IF NOT EXISTS idx_rewards_dataset ON rewards(dataset_id, at);
"""

with get_conn() as conn:
    for stmt in filter(None, (s.strip() for s in DDL.split(";"))):
        if stmt:
            conn.execute(stmt)
print("✅ rewards table ready")
