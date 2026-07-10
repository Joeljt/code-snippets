#!/usr/bin/env python
import pika
import sys

from pika.exchange_type import ExchangeType

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)
channel = connection.channel()

channel.exchange_declare(exchange='topic_logs', exchange_type=ExchangeType.topic)

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

binding_key = sys.argv[1] if len(sys.argv) > 1 else 'anonymous.info'
channel.queue_bind(exchange='topic_logs', queue=queue_name, routing_key=binding_key)

print(' [*] Waiting for logs. To exit press CTRL+C')

def callback(ch, method, properties, body):
    print(f" [x] {method.routing_key}:{body}")

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

channel.start_consuming()

# 启动两个消费者，一个只监听 anonymous.info 消息，写入日志，一个监听 anonymous.warning 和 anonymous.info，打印在控制台上
# uv run python -u receive_logs_topic.py anonymous.info > logs.log 可以将 anonymous.info 级别的消息打印到 logs.log 文件中
# 然后发消息的时候会发现，类型不同的消息因为无法命中 routing key，不会进入不匹配的队列

# rabbitmqctl list_bindings 输出：
# source_name	source_kind	destination_name	            destination_kind	routing_key	arguments
# topic_logs	exchange	amq.gen-Vd8IjLeabhO9NWIBbwuZdw	queue	            happy.#	    []
# topic_logs	exchange	amq.gen-PKRR6oK8LIF63TBflHjQpw	queue	            some.*.*	[]

# hash 表示任意数量的任意内容匹配
# 如果直接制定一个 # 作为 routing key，则表示匹配所有消息，相当于 fanout 模式

# * 表示一个单词的匹配，比如 some.*.* 表示 some. 后面跟着任意两个单词

# 如果 topic 模式下，但是 * 和 # 都没有使用，则表示精确匹配，相当于 direct 模式

# routing key 使用 . 做分割，比如 anonymous.info 表示 anonymous 和 info 两个单词
# 在这个基础上，* 和 # 可以任意组合，在这个基础上匹配其各自的特性即可
# * 是一个单词，# 是 0 或多个单词，其中 . 分隔完以后的空字符串也能算作一个单词
# 所以订阅 some.*，发消息的时候即使是 'some.' 也能命中，订阅 some.*.*，发消息的时候即使是 'some..' 也能命中
# 因为 split 之后，空字符串也能算作一个单词