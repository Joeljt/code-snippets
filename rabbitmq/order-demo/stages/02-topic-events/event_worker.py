#!/usr/bin/env python3
import pika

from topology import EX_ORDER_EVENTS, declare_topology

QUEUE = "order.events.log"


def on_message(channel, method, _properties, body):
    print(f"[event] key={method.routing_key}  order_id={body.decode()}")
    channel.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    declare_topology(channel)
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.queue_bind(queue=QUEUE, exchange=EX_ORDER_EVENTS, routing_key="order.#")
    channel.basic_consume(queue=QUEUE, on_message_callback=on_message, auto_ack=False)
    print("[*] event_worker waiting (bind order.#) ...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
