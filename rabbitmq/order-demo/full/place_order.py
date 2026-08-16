#!/usr/bin/env python3
"""下单：写库 + 发 order.created + 延迟关单检查。"""

from __future__ import annotations

import argparse
import sys

from connection import open_channel, publish_json
from db import create_order, get_order, init_db
from messages import build_payload
from topology import EX_ORDER_DELAY, EX_ORDER_EVENTS, declare_topology

DEFAULT_DELAY_MS = 15_000


def main() -> None:
    parser = argparse.ArgumentParser(description="Place a demo order")
    parser.add_argument("--vip", action="store_true", help="VIP 订单（发货时 priority=5）")
    parser.add_argument(
        "--bad-key",
        action="store_true",
        help="额外发一条 order.unknown，演示备份交换机",
    )
    parser.add_argument("--delay-ms", type=int, default=DEFAULT_DELAY_MS, help="未支付关单延迟（毫秒）")
    args = parser.parse_args()

    init_db()
    order_id = create_order(vip=args.vip)
    row = get_order(order_id)
    assert row is not None

    conn, ch = open_channel(publisher=True)
    declare_topology(ch)

    payload = build_payload(
        order_id=order_id,
        event="order.created",
        vip=bool(args.vip),
        qty=row["qty"],
    )
    publish_json(ch, exchange=EX_ORDER_EVENTS, routing_key="order.created", payload=payload)
    print(f"[x] order.created  order_id={order_id} vip={args.vip}")

    timeout_payload = build_payload(
        order_id=order_id,
        event="order.timeout",
        vip=bool(args.vip),
        qty=row["qty"],
    )
    publish_json(
        ch,
        exchange=EX_ORDER_DELAY,
        routing_key="order.timeout",
        payload=timeout_payload,
        headers={"x-delay": args.delay_ms},
    )
    print(f"[x] order.timeout scheduled delay={args.delay_ms}ms")

    if args.bad_key:
        bad = build_payload(order_id=order_id, event="order.unknown", vip=bool(args.vip))
        publish_json(ch, exchange=EX_ORDER_EVENTS, routing_key="order.unknown", payload=bad)
        print("[x] order.unknown sent (expect audit.unroutable)")

    conn.close()
    print(f"[*] Created {order_id}")


if __name__ == "__main__":
    main()
