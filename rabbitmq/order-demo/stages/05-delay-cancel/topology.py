import pika
from pika.exchange_type import ExchangeType

EX_EVENTS = "order.events"
EX_DELAY = "order.delay"
EX_CMD = "inventory.commands"
Q_TIMEOUT = "order.timeout"
Q_DEDUCT = "inventory.deduct"
QUORUM = {"x-queue-type": "quorum"}


def declare_topology(ch):
    ch.exchange_declare(exchange=EX_EVENTS, exchange_type=ExchangeType.topic, durable=True)
    ch.exchange_declare(
        exchange=EX_DELAY,
        exchange_type="x-delayed-message",
        durable=True,
        arguments={"x-delayed-type": "direct"},
    )
    ch.exchange_declare(exchange=EX_CMD, exchange_type=ExchangeType.direct, durable=True)
    ch.queue_declare(queue=Q_TIMEOUT, durable=True, arguments=QUORUM)
    ch.queue_declare(queue=Q_DEDUCT, durable=True, arguments=QUORUM)
    ch.queue_bind(Q_TIMEOUT, EX_DELAY, routing_key="order.timeout")
    ch.queue_bind(Q_DEDUCT, EX_CMD, routing_key="deduct")
