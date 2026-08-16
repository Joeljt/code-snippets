#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bootstrap  # noqa: F401

from connection import open_channel, parse_json
from db import is_processed, mark_processed
from topology import Q_AUDIT_UNROUTABLE, declare_topology


def on_message(ch, method, properties, body):
    if is_processed(properties.message_id):
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    payload = parse_json(body)
    print(
        f"[AE] unroutable  routing_key={method.routing_key} "
        f"order_id={payload.get('order_id')} event={payload.get('event')}"
    )
    mark_processed(properties.message_id)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    conn, ch = open_channel()
    declare_topology(ch)
    ch.basic_qos(prefetch_count=10)
    ch.basic_consume(queue=Q_AUDIT_UNROUTABLE, on_message_callback=on_message, auto_ack=False)
    print("[*] unroutable_worker waiting on audit.unroutable ...")
    ch.start_consuming()


if __name__ == "__main__":
    main()
