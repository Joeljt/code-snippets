#!/usr/bin/env python3
"""阶段 1：下单，消息进 order.created 队列（Default Exchange）。"""
import uuid

import pika

ORDER_QUEUE = "order.created"


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    channel.queue_declare(queue=ORDER_QUEUE, durable=True)

    order_id = f"ord_{uuid.uuid4().hex[:8]}"
    channel.basic_publish(exchange="", routing_key=ORDER_QUEUE, body=order_id.encode())
    print(f"[x] Sent order_id={order_id}")
    connection.close()


if __name__ == "__main__":
    main()
