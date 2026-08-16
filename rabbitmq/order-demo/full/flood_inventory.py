#!/usr/bin/env python3
"""路径 7：打满 inventory.deduct（reject-publish）。先停 inventory_worker。"""

from __future__ import annotations

import uuid

from connection import open_channel, publish_json
from messages import build_payload
from topology import EX_INVENTORY_COMMANDS, declare_topology


def main() -> None:
    conn, ch = open_channel(publisher=True)
    declare_topology(ch)

    for i in range(8):
        oid = f"ord_flood_inv_{i}_{uuid.uuid4().hex[:4]}"
        payload = build_payload(order_id=oid, event="inventory.deduct")
        try:
            publish_json(
                ch,
                exchange=EX_INVENTORY_COMMANDS,
                routing_key="deduct",
                payload=payload,
            )
            print(f"[x] flood deduct #{i + 1} ok -> {oid}")
        except SystemExit:
            print(f"[!] flood deduct #{i + 1} rejected (queue full)")
            break

    conn.close()


if __name__ == "__main__":
    main()
