#!/usr/bin/env python3
import pika

from db import init_db, is_processed, mark_processed
from topology import Q_DEDUCT, declare_topology


def on_message(ch, method, props, body):
    if props.message_id and is_processed(props.message_id):
        ch.basic_ack(method.delivery_tag)
        return
    oid = body.decode()
    print(f"[inventory] deducted {oid}")
    if props.message_id:
        mark_processed(props.message_id)
    ch.basic_ack(method.delivery_tag)


def main():
    init_db()
    conn = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    ch = conn.channel()
    declare_topology(ch)
    ch.basic_qos(prefetch_count=10)
    ch.basic_consume(Q_DEDUCT, on_message, auto_ack=False)
    print("[*] inventory_worker (idempotent ack after success)")
    ch.start_consuming()


if __name__ == "__main__":
    main()
