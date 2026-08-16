#!/usr/bin/env python3
"""往 shipping.jobs 塞 3 普通 + 1 VIP，演示优先级。"""
import pika
from topology import Q_SHIP, declare_topology

conn = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
ch = conn.channel()
declare_topology(ch)
for i in range(3):
    ch.basic_publish("", Q_SHIP, f"normal-{i}".encode(), properties=pika.BasicProperties(priority=1))
    print(f"[x] normal-{i} priority=1")
ch.basic_publish("", Q_SHIP, b"vip-order", properties=pika.BasicProperties(priority=5))
print("[x] vip-order priority=5")
conn.close()
