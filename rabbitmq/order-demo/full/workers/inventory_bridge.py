#!/usr/bin/env python3
"""Topic 事件 -> Direct 命令的 bridge。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bootstrap  # noqa: F401

from connection import open_channel, parse_json, publish_json
from db import is_processed, mark_processed
from messages import build_payload
from topology import EX_INVENTORY_COMMANDS, Q_INVENTORY_BRIDGE, declare_topology


def on_message(ch, method, properties, body):
    if is_processed(properties.message_id):
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    payload = parse_json(body)
    order_id = payload["order_id"]
    routing_key = method.routing_key

    if routing_key == "order.paid":
        cmd = "deduct"
        event = "inventory.deduct"
    elif routing_key == "order.cancelled":
        cmd = "restore"
        event = "inventory.restore"
    else:
        mark_processed(properties.message_id)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    out = build_payload(
        order_id=order_id,
        event=event,
        vip=payload.get("vip", False),
        qty=payload.get("qty", 1),
    )
    publish_json(ch, exchange=EX_INVENTORY_COMMANDS, routing_key=cmd, payload=out)
    print(f"[x] bridge {routing_key} -> {cmd}  order_id={order_id}")
    mark_processed(properties.message_id)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    conn, ch = open_channel(publisher=True)
    declare_topology(ch)
    ch.basic_qos(prefetch_count=10)
    ch.basic_consume(queue=Q_INVENTORY_BRIDGE, on_message_callback=on_message, auto_ack=False)
    print("[*] inventory_bridge waiting on order.paid / order.cancelled ...")
    ch.start_consuming()


if __name__ == "__main__":
    main()
