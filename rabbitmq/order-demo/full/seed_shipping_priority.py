#!/usr/bin/env python3
"""路径 3：往 shipping.jobs 塞 3 普通 + 1 VIP，演示优先级队列。"""

from __future__ import annotations

import uuid

from connection import open_channel, publish_json
from messages import build_payload
from topology import Q_SHIPPING_JOBS, declare_topology


def main() -> None:
    conn, ch = open_channel(publisher=True)
    declare_topology(ch)

    for i in range(3):
        oid = f"ord_seed_normal_{i}_{uuid.uuid4().hex[:6]}"
        payload = build_payload(order_id=oid, event="inventory.deducted", vip=False)
        publish_json(
            ch,
            exchange="",
            routing_key=Q_SHIPPING_JOBS,
            payload=payload,
            priority=1,
        )
        print(f"[x] seeded normal priority=1  {oid}")

    vip_oid = f"ord_seed_vip_{uuid.uuid4().hex[:6]}"
    vip_payload = build_payload(order_id=vip_oid, event="inventory.deducted", vip=True)
    publish_json(
        ch,
        exchange="",
        routing_key=Q_SHIPPING_JOBS,
        payload=vip_payload,
        priority=5,
    )
    print(f"[x] seeded VIP priority=5  {vip_oid}")

    conn.close()
    print("[*] Run shipping_worker --slow and watch VIP ship first.")


if __name__ == "__main__":
    main()
