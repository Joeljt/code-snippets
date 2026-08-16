import json
import sys
import uuid
from typing import Any, Optional

import pika

BROKER = pika.ConnectionParameters("localhost", heartbeat=30)


def open_channel(*, publisher: bool = False):
    conn = pika.BlockingConnection(BROKER)
    ch = conn.channel()
    if publisher:
        ch.confirm_delivery()  # BlockingConnection 下为 publish-and-wait
    return conn, ch


def publish(channel, exchange: str, routing_key: str, body: str, *, headers: Optional[dict] = None):
    props = pika.BasicProperties(
        delivery_mode=pika.DeliveryMode.Persistent,
        content_type="text/plain",
        message_id=str(uuid.uuid4()),
        headers=headers or {},
    )
    ok = channel.basic_publish(exchange=exchange, routing_key=routing_key, body=body.encode(), properties=props)
    if ok is False:
        print("[!] publish nack", file=sys.stderr)
        sys.exit(1)
