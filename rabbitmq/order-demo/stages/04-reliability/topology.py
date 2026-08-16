import pika
from pika.exchange_type import ExchangeType

EX_EVENTS = "order.events"
EX_CMD = "inventory.commands"
Q_DEDUCT = "inventory.deduct"
QUORUM = {"x-queue-type": "quorum"}


def declare_topology(ch):
    ch.exchange_declare(exchange=EX_EVENTS, exchange_type=ExchangeType.topic, durable=True)
    ch.exchange_declare(exchange=EX_CMD, exchange_type=ExchangeType.direct, durable=True)
    ch.queue_declare(queue=Q_DEDUCT, durable=True, arguments=QUORUM)
    ch.queue_bind(queue=Q_DEDUCT, exchange=EX_CMD, routing_key="deduct")
