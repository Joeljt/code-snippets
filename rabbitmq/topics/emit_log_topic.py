#!/usr/bin/env python
import pika
import sys

from pika.exchange_type import ExchangeType

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)
channel = connection.channel()

# 声明一个交换机，指定为 topic 模式，即主题模式
# topic 模式下，只有 publish 的 routing_key 和 subscribe 的 routing_key 部分匹配时，消息才会被传递到该队列
# 匹配规则：
# * 匹配一个单词
# # 匹配一个或多个单词
# 例如：
# routing_key: "kernel.info"
# subscribe 的 routing_key: "kernel.*" 会匹配
# subscribe 的 routing_key: "kernel.#" 会匹配
# subscribe 的 routing_key: "kernel.info" 会匹配
channel.exchange_declare(exchange='topic_logs', exchange_type=ExchangeType.topic)

# 获取命令行参数，如果没有提供，则使用默认值 info
severity = sys.argv[1] if len(sys.argv) > 1 else 'anonymous.info'
# 如果没有提供消息，则使用默认值 Hello World!
message = ' '.join(sys.argv[2:]) or 'Hello World!'
# 发布消息，指定交换机和路由键，使用 routing_key 作为主题
channel.basic_publish(exchange='topic_logs', routing_key=severity, body=message)
# 打印发送的消息
print(f"[x] Sent {severity}: {message}")