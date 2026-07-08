#!/usr/bin/env python3
import pika, sys, os

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='hello', durable=True, arguments={'x-queue-type': 'quorum'})

    def callback(ch, method, properties, body):
        print(f" [x] Received {body}")

    # 这里的 auto_ack 表示自动确认消息，如果为 True，则消费者收到消息后会自动确认消息，如果为 False，则需要手动确认消息。
    channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)