import sqlite3
import uuid
from pathlib import Path

DB = Path(__file__).resolve().parent / "stage5.sqlite"


def init_db():
    with sqlite3.connect(DB) as c:
        c.execute("CREATE TABLE IF NOT EXISTS orders (order_id TEXT PRIMARY KEY, status TEXT NOT NULL)")


def create_order() -> str:
    oid = f"ord_{uuid.uuid4().hex[:8]}"
    with sqlite3.connect(DB) as c:
        c.execute("INSERT INTO orders VALUES (?, 'unpaid')", (oid,))
    return oid


def mark_paid(oid: str) -> bool:
    with sqlite3.connect(DB) as c:
        return c.execute("UPDATE orders SET status='paid' WHERE order_id=? AND status='unpaid'", (oid,)).rowcount == 1


def mark_cancelled(oid: str) -> bool:
    with sqlite3.connect(DB) as c:
        return c.execute("UPDATE orders SET status='cancelled' WHERE order_id=? AND status='unpaid'", (oid,)).rowcount == 1


def get_status(oid: str) -> str | None:
    with sqlite3.connect(DB) as c:
        row = c.execute("SELECT status FROM orders WHERE order_id=?", (oid,)).fetchone()
        return row[0] if row else None
