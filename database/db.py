import sqlite3
from contextlib import contextmanager
from pathlib import Path

from config import DATABASE_PATH, INVOICES_DIR
from database.models import SCHEMA_SQL
from database.seed import seed_if_needed


def get_connection() -> sqlite3.Connection:
    INVOICES_DIR.mkdir(parents=True, exist_ok=True)
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db_session() as conn:
        conn.executescript(SCHEMA_SQL)
        seed_if_needed(conn)
