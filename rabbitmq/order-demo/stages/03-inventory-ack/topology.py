import pika
from pika.exchange_type import ExchangeType

EX_ORDER_EVENTS = "order.events"
EX_INVENTORY_COMMANDS = "inventory.commands"
Q_INVENTORY_DEDUCT = "inventory.deduct"


def declare_topology(channel):
    channel.exchange_declare(exchange=EX_ORDER_EVENTS, exchange_type=ExchangeType.topic, durable=True)
    channel.exchange_declare(exchange=EX_INVENTORY_COMMANDS, exchange_type=ExchangeType.direct, durable=True)
    channel.queue_declare(queue=Q_INVENTORY_DEDUCT, durable=True)
    channel.queue_bind(queue=Q_INVENTORY_DEDUCT, exchange=EX_INVENTORY_COMMANDS, routing_key="deduct")
