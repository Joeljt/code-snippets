import sqlite3
import uuid
from pathlib import Path

DB = Path(__file__).resolve().parent / "stage4.sqlite"


def init_db():
    with sqlite3.connect(DB) as c:
        c.execute("CREATE TABLE IF NOT EXISTS orders (order_id TEXT PRIMARY KEY, status TEXT NOT NULL)")
        c.execute("CREATE TABLE IF NOT EXISTS processed (message_id TEXT PRIMARY KEY)")


def create_order() -> str:
    oid = f"ord_{uuid.uuid4().hex[:8]}"
    with sqlite3.connect(DB) as c:
        c.execute("INSERT INTO orders VALUES (?, 'unpaid')", (oid,))
    return oid


def mark_paid(order_id: str) -> bool:
    with sqlite3.connect(DB) as c:
        cur = c.execute("UPDATE orders SET status='paid' WHERE order_id=? AND status='unpaid'", (order_id,))
        return cur.rowcount == 1


def is_processed(mid: str) -> bool:
    with sqlite3.connect(DB) as c:
        return c.execute("SELECT 1 FROM processed WHERE message_id=?", (mid,)).fetchone() is not None


def mark_processed(mid: str):
    with sqlite3.connect(DB) as c:
        c.execute("INSERT OR IGNORE INTO processed VALUES (?)", (mid,))
