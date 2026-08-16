#!/usr/bin/env python3
"""阶段 1：打印收到的订单号。"""
import pika

ORDER_QUEUE = "order.created"


def on_message(channel, method, _properties, body):
    print(f"[order] received {body.decode()}")
    channel.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    channel.queue_declare(queue=ORDER_QUEUE, durable=True)
    channel.basic_consume(queue=ORDER_QUEUE, on_message_callback=on_message, auto_ack=False)
    print(f"[*] Waiting on {ORDER_QUEUE}. Ctrl+C to exit.")
    channel.start_consuming()


if __name__ == "__main__":
    main()
