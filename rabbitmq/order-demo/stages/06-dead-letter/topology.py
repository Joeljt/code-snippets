import pika
from pika.exchange_type import ExchangeType

EX_CMD = "inventory.commands"
EX_DLX = "order.dlx"
Q_DEDUCT = "inventory.deduct"
Q_DEAD = "order.dead"
QUORUM = {"x-queue-type": "quorum"}


def declare_topology(ch):
    ch.exchange_declare(EX_DLX, ExchangeType.topic, durable=True)
    ch.exchange_declare(EX_CMD, ExchangeType.direct, durable=True)
    ch.queue_declare(
        Q_DEDUCT, durable=True,
        arguments={**QUORUM, "x-dead-letter-exchange": EX_DLX, "x-delivery-limit": 3},
    )
    ch.queue_declare(Q_DEAD, durable=True, arguments=QUORUM)
    ch.queue_bind(Q_DEDUCT, EX_CMD, routing_key="deduct")
    ch.queue_bind(Q_DEAD, EX_DLX, routing_key="#")
