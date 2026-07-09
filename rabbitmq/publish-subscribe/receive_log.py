#!/usr/bin/env python
import pika
from pika.exchange_type import ExchangeType

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)
channel = connection.channel()

# 声明同名交换机，用于接收消息
channel.exchange_declare(exchange='logs', exchange_type=ExchangeType.fanout)

# 不指定队列名称，让系统随机生成名称，并将该队列与交换机绑定，从而实现 subscribe 的效果
# 使用 exclusive=True 参数，表示当消费者断开连接时，队列会自动删除
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

channel.queue_bind(exchange='logs', queue=queue_name)

print(' [*] Waiting for logs. To exit press CTRL+C')

def callback(ch, method, properties, body):
    print(f" [x] {body}")

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

channel.start_consuming()

# 启动两个消费者，可以看到每个消费者都收到了相同的消息
# uv run python -u receive_log.py > logs.log 可以将日志打印到 logs.log 文件中

# docker exec -it some-rabbit rabbitmqctl list_queues 可以查看队列信息
# docker exec -it some-rabbit rabbitmqctl list_exchanges 可以查看交换机信息
# docker exec -it some-rabbit rabbitmqctl list_bindings 可以查看绑定信息

# list_exchanges 输出：
# name	type
#logs	fanout