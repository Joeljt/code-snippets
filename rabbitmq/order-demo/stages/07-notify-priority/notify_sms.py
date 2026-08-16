#!/usr/bin/env python3
import pika
from topology import Q_SMS, declare_topology


def on_message(ch, method, _p, body):
    print(f"[SMS] {body.decode()}")
    ch.basic_ack(method.delivery_tag)


def main():
    conn = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    ch = conn.channel()
    declare_topology(ch)
    ch.basic_consume(Q_SMS, on_message, auto_ack=False)
    print("[*] notify_sms waiting ...")
    ch.start_consuming()


if __name__ == "__main__":
    main()
