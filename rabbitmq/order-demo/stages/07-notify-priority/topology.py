import pika
from pika.exchange_type import ExchangeType

EX_NOTIFY = "notifications"
Q_SHIP = "shipping.jobs"
Q_SMS = "notify.sms"


def declare_topology(ch):
    ch.exchange_declare(EX_NOTIFY, ExchangeType.fanout, durable=True)
    ch.queue_declare(Q_SHIP, durable=True, arguments={"x-max-priority": 5})
    ch.queue_declare(Q_SMS, durable=True)
    ch.queue_bind(Q_SMS, EX_NOTIFY)
