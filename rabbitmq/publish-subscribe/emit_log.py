#!/usr/bin/env python
import pika
import sys

from pika.exchange_type import ExchangeType

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)
channel = connection.channel()

# 声明一个交换机，指定为 fanout 模式，即发布订阅模式
# 这里的交换机需要给消费者也声明并绑定上，就类似订阅了这个交换机的广播消息
channel.exchange_declare(exchange='logs', exchange_type=ExchangeType.fanout)

message = ' '.join(sys.argv[1:]) or "info: Hello World!"
channel.basic_publish(exchange='logs', routing_key='', body=message)
print(f"[x] Sent {message}")

connection.close()