#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bootstrap  # noqa: F401

from connection import open_channel, parse_json, publish_json
from db import get_order, init_db, is_processed, mark_cancelled, mark_processed
from messages import build_payload
from topology import EX_ORDER_EVENTS, Q_TIMEOUT, declare_topology


def on_message(ch, method, properties, body):
    if is_processed(properties.message_id):
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    payload = parse_json(body)
    order_id = payload["order_id"]
    init_db()

    if mark_cancelled(order_id):
        out = build_payload(
            order_id=order_id,
            event="order.cancelled",
            vip=payload.get("vip", False),
            qty=payload.get("qty", 1),
        )
        publish_json(ch, exchange=EX_ORDER_EVENTS, routing_key="order.cancelled", payload=out)
        print(f"[x] order.cancelled (timeout)  order_id={order_id}")
    else:
        row = get_order(order_id)
        status = row["status"] if row else "missing"
        print(f"[*] timeout skipped  order_id={order_id} status={status}")

    mark_processed(properties.message_id)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    init_db()
    conn, ch = open_channel(publisher=True)
    declare_topology(ch)
    ch.basic_qos(prefetch_count=10)
    ch.basic_consume(queue=Q_TIMEOUT, on_message_callback=on_message, auto_ack=False)
    print("[*] timeout_worker waiting on order.timeout ...")
    ch.start_consuming()


if __name__ == "__main__":
    main()
