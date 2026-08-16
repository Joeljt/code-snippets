"""阶段 2：只声明 order.events Topic 交换机。"""
import pika
from pika.exchange_type import ExchangeType

EX_ORDER_EVENTS = "order.events"


def declare_topology(channel):
    channel.exchange_declare(exchange=EX_ORDER_EVENTS, exchange_type=ExchangeType.topic, durable=True)
