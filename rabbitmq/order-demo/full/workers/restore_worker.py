#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bootstrap  # noqa: F401

from connection import open_channel, parse_json
from db import init_db, is_processed, mark_processed, restore_inventory
from topology import Q_INVENTORY_RESTORE, declare_topology


def on_message(ch, method, properties, body):
    if is_processed(properties.message_id):
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    payload = parse_json(body)
    order_id = payload["order_id"]
    sku = payload.get("sku", "SKU-DEMO")
    qty = payload.get("qty", 1)

    init_db()
    restored = restore_inventory(order_id, sku, qty)
    if restored:
        print(f"[x] inventory restored  order_id={order_id}")
    else:
        print(f"[*] restore skipped (not deducted)  order_id={order_id}")

    mark_processed(properties.message_id)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    init_db()
    conn, ch = open_channel()
    declare_topology(ch)
    ch.basic_qos(prefetch_count=10)
    ch.basic_consume(queue=Q_INVENTORY_RESTORE, on_message_callback=on_message, auto_ack=False)
    print("[*] restore_worker waiting on inventory.restore ...")
    ch.start_consuming()


if __name__ == "__main__":
    main()
