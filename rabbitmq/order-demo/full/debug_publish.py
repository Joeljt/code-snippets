#!/usr/bin/env python3
"""Default Exchange 对照：exchange='' + routing_key=队列名。"""

from __future__ import annotations

import argparse

from connection import open_channel, publish_json
from messages import build_payload
from topology import Q_NOTIFY_SMS, declare_topology


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish via default exchange")
    parser.add_argument("--queue", default=Q_NOTIFY_SMS, help="目标队列名")
    parser.add_argument("--order-id", default="ord_debug", help="演示用 order_id")
    args = parser.parse_args()

    conn, ch = open_channel(publisher=True)
    declare_topology(ch)
    payload = build_payload(order_id=args.order_id, event="debug.default_exchange")
    publish_json(ch, exchange="", routing_key=args.queue, payload=payload)
    conn.close()
    print(f"[x] default exchange -> {args.queue}")


if __name__ == "__main__":
    main()
