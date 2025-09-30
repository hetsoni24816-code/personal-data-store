# test_permissions.py
from db_init import init_schema
from db import get_conn
from security import hash_password
from permissions import grant_access, revoke_access, set_trusted_orgs, list_trusted_org_ids
from audit import log_event

# 1) ensure schema
init_schema()

# 2) seed one user (owner) and one org
with get_conn() as conn:
    conn.execute("INSERT OR IGNORE INTO users(id,role,name,email,password_hash,verified,created_at) VALUES(100,'user','Owner','owner@test','x',1,datetime('now'))")
    conn.execute("INSERT OR IGNORE INTO users(id,role,name,email,password_hash,verified,created_at) VALUES(200,'org','Org A','orga@test','x',1,datetime('now'))")
    conn.execute("INSERT OR IGNORE INTO users(id,role,name,email,password_hash,verified,created_at) VALUES(201,'org','Org B','orgb@test','x',1,datetime('now'))")
    # minimal dataset row for owner
    conn.execute("INSERT OR IGNORE INTO datasets(id,owner_id,name,content_enc,visibility,version,created_at) VALUES(1,100,'demo.txt',x'00','Trusted',1,datetime('now'))")

# 3) bulk set
print(set_trusted_orgs(dataset_id=1, owner_id=100, new_org_ids=[200,201]))
print(list_trusted_org_ids(1))

# 4) revoke one
revoke_access(dataset_id=1, owner_id=100, org_id=201)
print(list_trusted_org_ids(1))
