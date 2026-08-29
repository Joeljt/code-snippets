#!/usr/bin/env python3
import argparse
import time
import pika

from topology import EX_NOTIFY, Q_SHIP, declare_topology


def on_ship(ch, method, props, body, slow):
    pri = props.priority or 0
    if slow:
        time.sleep(2)
    print(f"[ship] {body.decode()} priority={pri}")
    ch.basic_publish(EX_NOTIFY, "", body, properties=pika.BasicProperties(delivery_mode=2))
    ch.basic_ack(method.delivery_tag)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slow", action="store_true")
    args = p.parse_args()
    conn = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    ch = conn.channel()
    declare_topology(ch)
    ch.basic_qos(prefetch_count=1)  # 优先级必须 prefetch=1
    ch.basic_consume(Q_SHIP, lambda c, m, pr, b: on_ship(c, m, pr, b, args.slow), auto_ack=False)
    print("[*] shipping_worker (--slow to observe VIP first)")
    ch.start_consuming()


if __name__ == "__main__":
    main()
