#!/usr/bin/env python3
import time

import pika

from topology import Q_INVENTORY_DEDUCT, declare_topology


def on_message(channel, method, _properties, body):
    order_id = body.decode()
    print(f"[inventory] deducting order_id={order_id} ...")
    time.sleep(1)  # 模拟耗时，便于观察 prefetch
    print(f"[inventory] done order_id={order_id}")
    channel.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    declare_topology(channel)
    # prefetch=1：处理完一条 ACK 后才拿下一条（能者多劳）
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=Q_INVENTORY_DEDUCT, on_message_callback=on_message, auto_ack=False)
    print("[*] inventory_worker waiting (manual ack, prefetch=1) ...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
