#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bootstrap  # noqa: F401

from connection import open_channel, parse_json, publish_json
from db import deduct_inventory, init_db, is_processed, mark_processed
from messages import build_payload
from topology import EX_ORDER_EVENTS, Q_INVENTORY_DEDUCT, declare_topology


def on_message(ch, method, properties, body, *, poison: bool):
    if is_processed(properties.message_id):
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    payload = parse_json(body)
    order_id = payload["order_id"]
    sku = payload.get("sku", "SKU-DEMO")
    qty = payload.get("qty", 1)
    vip = payload.get("vip", False)

    if poison:
        print(f"[!] poison fail  order_id={order_id}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        return

    init_db()
    deduct_inventory(order_id, sku, qty)

    out = build_payload(order_id=order_id, event="inventory.deducted", vip=vip, qty=qty, sku=sku)
    priority = 5 if vip else 1
    publish_json(
        ch,
        exchange=EX_ORDER_EVENTS,
        routing_key="inventory.deducted",
        payload=out,
        priority=priority,
    )
    print(f"[x] inventory.deducted  order_id={order_id} priority={priority}")
    mark_processed(properties.message_id)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--poison", action="store_true", help="故意失败，演示 x-delivery-limit 进死信")
    args = parser.parse_args()

    init_db()
    conn, ch = open_channel(publisher=True)
    declare_topology(ch)
    ch.basic_qos(prefetch_count=10)

    def callback(ch, method, properties, body):
        on_message(ch, method, properties, body, poison=args.poison)

    ch.basic_consume(queue=Q_INVENTORY_DEDUCT, on_message_callback=callback, auto_ack=False)
    mode = "POISON" if args.poison else "normal"
    print(f"[*] inventory_worker ({mode}) waiting on inventory.deduct ...")
    ch.start_consuming()


if __name__ == "__main__":
    main()
