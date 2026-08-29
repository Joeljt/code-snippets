#!/usr/bin/env python3
import argparse
import pika

from topology import Q_DEDUCT, declare_topology


def on_message(ch, method, _p, body, poison):
    oid = body.decode()
    if poison:
        print(f"[!] poison fail  {oid}")
        ch.basic_nack(method.delivery_tag, requeue=True)
        return
    print(f"[inventory] ok  {oid}")
    ch.basic_ack(method.delivery_tag)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--poison", action="store_true")
    args = p.parse_args()
    conn = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    ch = conn.channel()
    declare_topology(ch)
    ch.basic_qos(prefetch_count=10)
    ch.basic_consume(Q_DEDUCT, lambda ch, m, p, b: on_message(ch, m, p, b, args.poison), auto_ack=False)
    print(f"[*] inventory_worker poison={args.poison}")
    ch.start_consuming()


if __name__ == "__main__":
    main()
