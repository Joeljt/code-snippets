#!/usr/bin/env python3
"""支付订单。"""

from __future__ import annotations

import argparse
import sys

from connection import open_channel, publish_json
from db import get_order, init_db, mark_paid
from messages import build_payload
from topology import EX_ORDER_EVENTS, declare_topology


def main() -> None:
    parser = argparse.ArgumentParser(description="Pay for an order")
    parser.add_argument("order_id", help="订单 ID")
    args = parser.parse_args()

    init_db()
    row = get_order(args.order_id)
    if row is None:
        print(f"[!] Order not found: {args.order_id}", file=sys.stderr)
        sys.exit(1)

    result = mark_paid(args.order_id)
    if result == "cancelled":
        print(f"[!] Order already cancelled: {args.order_id}", file=sys.stderr)
        sys.exit(1)
    if result == "paid" and row["status"] in ("paid", "shipped"):
        print(f"[*] Already paid (idempotent): {args.order_id}")
        sys.exit(0)

    conn, ch = open_channel(publisher=True)
    declare_topology(ch)
    payload = build_payload(
        order_id=args.order_id,
        event="order.paid",
        vip=bool(row["vip"]),
        qty=row["qty"],
    )
    publish_json(ch, exchange=EX_ORDER_EVENTS, routing_key="order.paid", payload=payload)
    conn.close()
    print(f"[x] order.paid  order_id={args.order_id}")


if __name__ == "__main__":
    main()
