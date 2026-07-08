#!/usr/bin/env python
import pika
import time

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True, arguments={'x-queue-type': 'quorum'})
print(' [*] Waiting for messages. To exit press CTRL+C')


def callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")
    time.sleep(body.count(b'.'))
    print(" [x] Done")
    # 手动确认消息，告诉 RabbitMQ 已经处理完消息了，可以删除它了
    # 如果是 auto_ack=True，则消费者收到消息后会自动确认消息，但是消息可能没有处理完，这种情况会导致消息丢失
    ch.basic_ack(delivery_tag=method.delivery_tag)


# 设置预取计数为1，表示每个消费者在接收到下一个消息之前，只能处理一个消息。
# 在轮询顺序分发消息时，如果某个消费者还在消费其他任务，则会跳过它，发送给下一个空闲消费者，避免阻塞
channel.basic_qos(prefetch_count=1)

channel.basic_consume(queue='task_queue', on_message_callback=callback)

channel.start_consuming()