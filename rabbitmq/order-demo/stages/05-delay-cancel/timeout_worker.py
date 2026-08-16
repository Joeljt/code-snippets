#!/usr/bin/env python3
import pika

from db import get_status, init_db, mark_cancelled
from topology import Q_TIMEOUT, declare_topology


def on_message(ch, method, _p, body):
    oid = body.decode()
    init_db()
    if mark_cancelled(oid):
        print(f"[x] order.cancelled (timeout)  {oid}")
    else:
        print(f"[*] timeout skip  {oid} status={get_status(oid)}")
    ch.basic_ack(method.delivery_tag)


def main():
    init_db()
    conn = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    ch = conn.channel()
    declare_topology(ch)
    ch.basic_consume(Q_TIMEOUT, on_message, auto_ack=False)
    print("[*] timeout_worker waiting ...")
    ch.start_consuming()


if __name__ == "__main__":
    main()
