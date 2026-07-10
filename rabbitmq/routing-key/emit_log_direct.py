#!/usr/bin/env python
import pika
import sys

from pika.exchange_type import ExchangeType

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)
channel = connection.channel()

# 声明一个交换机，指定为 direct 模式，即路由模式
# direct 模式下，只有 publish 的 routing_key 和 subscribe 的 routing_key 完全匹配时，消息才会被传递到该队列
# 否则消息会被丢弃
channel.exchange_declare(exchange='direct_logs', exchange_type=ExchangeType.direct)

# 获取命令行参数，如果没有提供，则使用默认值 info
severity = sys.argv[1] if len(sys.argv) > 1 else 'info'
# 如果没有提供消息，则使用默认值 Hello World!
message = ' '.join(sys.argv[2:]) or 'Hello World!'
# 发布消息，指定交换机和路由键
channel.basic_publish(exchange='direct_logs', routing_key=severity, body=message)
# 打印发送的消息
print(f"[x] Sent {severity}: {message}")

connection.close()