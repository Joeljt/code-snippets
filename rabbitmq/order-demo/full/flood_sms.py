#!/usr/bin/env python3
"""路径 6：打满 notify.sms（drop-head + DLX maxlen）。先停 notify_sms worker。"""

from __future__ import annotations

import uuid

from connection import open_channel, publish_json
from messages import build_payload
from topology import Q_NOTIFY_SMS, declare_topology


def main() -> None:
    conn, ch = open_channel(publisher=True)
    declare_topology(ch)

    for i in range(8):
        oid = f"ord_flood_sms_{i}_{uuid.uuid4().hex[:4]}"
        payload = build_payload(order_id=oid, event="notify.flood")
        publish_json(ch, exchange="", routing_key=Q_NOTIFY_SMS, payload=payload)
        print(f"[x] flood sms #{i + 1} -> {oid}")

    conn.close()
    print("[*] notify.sms keeps latest 5; older messages -> order.dead (reason=maxlen)")


if __name__ == "__main__":
    main()
