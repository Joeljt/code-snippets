#!/usr/bin/env python3
"""阶段 6 辅助：往 deduct 队列塞一条测试消息。"""
import pika
from topology import EX_CMD, declare_topology

oid = "ord_poison_test"
conn = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
ch = conn.channel()
declare_topology(ch)
ch.basic_publish(EX_CMD, "deduct", oid.encode(), properties=pika.BasicProperties(delivery_mode=2))
print(f"[x] sent deduct {oid}")
conn.close()
