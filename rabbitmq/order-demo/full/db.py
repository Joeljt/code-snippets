"""SQLite 状态：订单状态机、库存、消费幂等。"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "order-demo.sqlite"
DEMO_SKU = "SKU-DEMO"
INITIAL_STOCK = 1000


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                vip INTEGER NOT NULL DEFAULT 0,
                sku TEXT NOT NULL,
                qty INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS inventory (
                sku TEXT PRIMARY KEY,
                qty INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS inventory_deducted (
                order_id TEXT PRIMARY KEY
            );
            CREATE TABLE IF NOT EXISTS processed_ids (
                message_id TEXT PRIMARY KEY
            );
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO inventory (sku, qty) VALUES (?, ?)",
            (DEMO_SKU, INITIAL_STOCK),
        )


def create_order(*, vip: bool = False, qty: int = 1) -> str:
    order_id = f"ord_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO orders (order_id, status, vip, sku, qty, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (order_id, "unpaid", int(vip), DEMO_SKU, qty, now),
        )
    return order_id


def get_order(order_id: str) -> sqlite3.Row | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
    return row


def mark_paid(order_id: str) -> str:
    """返回当前状态：paid（新支付或已支付）、cancelled、missing。"""
    with _connect() as conn:
        row = conn.execute("SELECT status FROM orders WHERE order_id = ?", (order_id,)).fetchone()
        if row is None:
            return "missing"
        status = row["status"]
        if status == "paid" or status == "shipped":
            return "paid"
        if status == "cancelled":
            return "cancelled"
        cur = conn.execute(
            "UPDATE orders SET status = 'paid' WHERE order_id = ? AND status = 'unpaid'",
            (order_id,),
        )
        if cur.rowcount == 0:
            row = conn.execute("SELECT status FROM orders WHERE order_id = ?", (order_id,)).fetchone()
            return row["status"] if row else "missing"
        return "paid"


def mark_cancelled(order_id: str) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE orders SET status = 'cancelled' WHERE order_id = ? AND status = 'unpaid'",
            (order_id,),
        )
        return cur.rowcount == 1


def mark_shipped(order_id: str) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE orders SET status = 'shipped' WHERE order_id = ? AND status = 'paid'",
            (order_id,),
        )
        return cur.rowcount == 1


def deduct_inventory(order_id: str, sku: str, qty: int) -> bool:
    """已扣过则返回 False（幂等）。"""
    with _connect() as conn:
        exists = conn.execute(
            "SELECT 1 FROM inventory_deducted WHERE order_id = ?", (order_id,)
        ).fetchone()
        if exists:
            return False
        conn.execute("INSERT INTO inventory_deducted (order_id) VALUES (?)", (order_id,))
        conn.execute("UPDATE inventory SET qty = qty - ? WHERE sku = ?", (qty, sku))
        return True


def restore_inventory(order_id: str, sku: str, qty: int) -> bool:
    """未扣过库存则无需还，返回 False。"""
    with _connect() as conn:
        exists = conn.execute(
            "SELECT 1 FROM inventory_deducted WHERE order_id = ?", (order_id,)
        ).fetchone()
        if not exists:
            return False
        conn.execute("DELETE FROM inventory_deducted WHERE order_id = ?", (order_id,))
        conn.execute("UPDATE inventory SET qty = qty + ? WHERE sku = ?", (qty, sku))
        return True


def is_processed(message_id: str | None) -> bool:
    if not message_id:
        return False
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM processed_ids WHERE message_id = ?", (message_id,)
        ).fetchone()
    return row is not None


def mark_processed(message_id: str | None) -> None:
    if not message_id:
        return
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO processed_ids (message_id) VALUES (?)",
            (message_id,),
        )
