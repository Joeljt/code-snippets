#!/usr/bin/env python3
import sys

import pika

from topology import EX_INVENTORY_COMMANDS, EX_ORDER_EVENTS, declare_topology


def main():
    if len(sys.argv) < 2:
        print("Usage: python pay.py <order_id>")
        sys.exit(1)
    order_id = sys.argv[1]
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    declare_topology(channel)
    channel.basic_publish(exchange=EX_ORDER_EVENTS, routing_key="order.paid", body=order_id.encode())
    # 阶段 3 简化：支付后直接发扣库存命令（完整版会用 bridge 从事件转命令）
    channel.basic_publish(exchange=EX_INVENTORY_COMMANDS, routing_key="deduct", body=order_id.encode())
    print(f"[x] order.paid + inventory.deduct  order_id={order_id}")
    connection.close()


if __name__ == "__main__":
    main()
