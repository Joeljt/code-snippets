#!/usr/bin/env python3
import argparse
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bootstrap  # noqa: F401

from connection import open_channel, parse_json, publish_json
from db import init_db, is_processed, mark_processed, mark_shipped
from messages import build_payload
from topology import EX_NOTIFICATIONS, EX_ORDER_EVENTS, Q_SHIPPING_JOBS, declare_topology


def on_message(ch, method, properties, body, *, slow: bool):
    if is_processed(properties.message_id):
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    payload = parse_json(body)
    order_id = payload["order_id"]
    vip = payload.get("vip", False)
    priority = properties.priority or (5 if vip else 1)

    if slow:
        time.sleep(2)

    init_db()
    shipped_ok = mark_shipped(order_id)
    if shipped_ok:
        shipped = build_payload(order_id=order_id, event="order.shipped", vip=vip, qty=payload.get("qty", 1))
        publish_json(ch, exchange=EX_ORDER_EVENTS, routing_key="order.shipped", payload=shipped)

        notify = build_payload(order_id=order_id, event="order.shipped.notify", vip=vip)
        publish_json(ch, exchange=EX_NOTIFICATIONS, routing_key="", payload=notify)
        print(f"[x] shipped + notify  order_id={order_id} priority={priority}")
    else:
        # seed_shipping_priority 演示单不在 DB，仍打印优先级观察日志
        print(f"[x] demo ship  order_id={order_id} priority={priority} (no db row)")

    mark_processed(properties.message_id)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slow", action="store_true", help="每条 sleep 2s，便于观察 VIP 插队")
    args = parser.parse_args()

    init_db()
    conn, ch = open_channel(publisher=True)
    declare_topology(ch)
    # 优先级队列必须 prefetch=1，否则消息全被抓走后排序失效
    ch.basic_qos(prefetch_count=1)

    def callback(ch, method, properties, body):
        on_message(ch, method, properties, body, slow=args.slow)

    ch.basic_consume(queue=Q_SHIPPING_JOBS, on_message_callback=callback, auto_ack=False)
    mode = "slow" if args.slow else "normal"
    print(f"[*] shipping_worker ({mode}) waiting on shipping.jobs ...")
    ch.start_consuming()


if __name__ == "__main__":
    main()
