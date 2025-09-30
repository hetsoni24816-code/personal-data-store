# db.py
import sqlite3
from contextlib import contextmanager

DB_PATH = "pds.db"

PRAGMAS = [
    ("journal_mode", "WAL"),     # allows readers while writing
    ("synchronous", "NORMAL"),   # good perf vs safety for prototypes
    ("foreign_keys", "ON"),
    ("busy_timeout", "5000"),    # wait up to 5s if the db is busy
    ("temp_store", "MEMORY"),
]

def _apply_pragmas(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    for k, v in PRAGMAS:
        cur.execute(f"PRAGMA {k}={v};")
    cur.close()

@contextmanager
def get_conn():
    # check_same_thread=False so Streamlit threads can use it
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    _apply_pragmas(conn)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

