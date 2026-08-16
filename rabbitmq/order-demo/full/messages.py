"""统一消息体构造。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from db import DEMO_SKU


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_payload(
    *,
    order_id: str,
    event: str,
    vip: bool = False,
    qty: int = 1,
    sku: str = DEMO_SKU,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "order_id": order_id,
        "sku": sku,
        "qty": qty,
        "vip": vip,
        "event": event,
        "ts": now_iso(),
    }
    if extra:
        payload.update(extra)
    return payload
