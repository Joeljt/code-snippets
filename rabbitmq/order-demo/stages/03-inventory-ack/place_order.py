#!/usr/bin/env python3
import uuid

import pika

from topology import EX_ORDER_EVENTS, declare_topology


def main():
    order_id = f"ord_{uuid.uuid4().hex[:8]}"
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    declare_topology(channel)
    channel.basic_publish(exchange=EX_ORDER_EVENTS, routing_key="order.created", body=order_id.encode())
    print(f"[x] order.created  order_id={order_id}")
    print(f"[*] Pay: python pay.py {order_id}")
    connection.close()


if __name__ == "__main__":
    main()
