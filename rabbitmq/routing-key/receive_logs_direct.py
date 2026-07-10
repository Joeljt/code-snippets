#!/usr/bin/env python
import pika
import sys

from pika.exchange_type import ExchangeType

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)
channel = connection.channel()

channel.exchange_declare(exchange='direct_logs', exchange_type=ExchangeType.direct)

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

severities = sys.argv[1:]
if not severities:
    sys.stderr.write("Usage: %s [info] [warning] [error]\n" % sys.argv[0])
    sys.exit(1)

for severity in severities:
    channel.queue_bind(exchange='direct_logs', queue=queue_name, routing_key=severity)

print(' [*] Waiting for logs. To exit press CTRL+C')

def callback(ch, method, properties, body):
    print(f" [x] {method.routing_key}:{body}")

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

channel.start_consuming()

# 启动两个消费者，一个只监听 error 消息，写入日志，一个监听 warning 和 info，打印在控制台上
# uv run python -u receive_logs_direct.py error > logs.log 可以将 error 级别的消息打印到 logs.log 文件中
# 然后发消息的时候会发现，类型不同的消息因为无法命中 routing key，不会进入不匹配的队列

# rabbitmqctl list_bindings 输出：
# source_name	source_kind	destination_name	            destination_kind	routing_key	arguments
# direct_logs	exchange	amq.gen-UDvWsxWjXovXm6rM10w5XQ	queue	error	[]
# direct_logs	exchange	amq.gen-DhpH5Ybp2e-UVIT3_DGyWw	queue	info	[]
# direct_logs	exchange	amq.gen-DhpH5Ybp2e-UVIT3_DGyWw	queue	warning	[]