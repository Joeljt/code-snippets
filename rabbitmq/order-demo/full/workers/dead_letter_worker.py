#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bootstrap  # noqa: F401

from connection import open_channel, parse_json
from db import is_processed, mark_processed
from topology import Q_ORDER_DEAD, declare_topology


def on_message(ch, method, properties, body):
    if is_processed(properties.message_id):
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    payload = parse_json(body)
    x_death = (properties.headers or {}).get("x-death")
    print(f"[DLX] order_id={payload.get('order_id')} x-death={json.dumps(x_death, ensure_ascii=False)}")
    mark_processed(properties.message_id)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    conn, ch = open_channel()
    declare_topology(ch)
    ch.basic_qos(prefetch_count=10)
    ch.basic_consume(queue=Q_ORDER_DEAD, on_message_callback=on_message, auto_ack=False)
    print("[*] dead_letter_worker waiting on order.dead ...")
    ch.start_consuming()


if __name__ == "__main__":
    main()
