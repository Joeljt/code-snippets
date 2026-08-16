#!/usr/bin/env python3
import json
import pika

from topology import Q_DEAD, declare_topology


def on_message(ch, method, props, body):
    print(f"[DLX] body={body.decode()}  x-death={json.dumps((props.headers or {}).get('x-death'), ensure_ascii=False)}")
    ch.basic_ack(method.delivery_tag)


def main():
    conn = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    ch = conn.channel()
    declare_topology(ch)
    ch.basic_consume(Q_DEAD, on_message, auto_ack=False)
    print("[*] dead_letter_worker waiting ...")
    ch.start_consuming()


if __name__ == "__main__":
    main()
