import uuid
import pika

BROKER = pika.ConnectionParameters("localhost", heartbeat=30)
DELAY_MS = 15000


def pub(ch, ex, rk, body, *, headers=None):
    ch.confirm_delivery()
    ok = ch.basic_publish(
        ex, rk, body.encode(),
        properties=pika.BasicProperties(
            delivery_mode=2, message_id=str(uuid.uuid4()), headers=headers or {},
        ),
    )
    if ok is False:
        raise SystemExit("publish nack")
