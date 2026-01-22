import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db(db_path: str):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()
