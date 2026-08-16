"""Connection / Channel 封装：每进程 1 Connection + 1 Channel，不跨线程共享。"""

from __future__ import annotations

import json
import sys
import uuid
from typing import Any, Optional

import pika

BROKER_HOST = "localhost"
BROKER_PORT = 5672
HEARTBEAT = 30


def connect() -> pika.BlockingConnection:
    params = pika.ConnectionParameters(
        host=BROKER_HOST,
        port=BROKER_PORT,
        heartbeat=HEARTBEAT,
        connection_attempts=3,
        retry_delay=2,
        socket_timeout=5,
    )
    return pika.BlockingConnection(params)


def open_channel(publisher: bool = False) -> tuple[pika.BlockingConnection, pika.channel.Channel]:
    print(f"[*] Connecting to RabbitMQ at {BROKER_HOST}:{BROKER_PORT} ...", flush=True)
    connection = connect()
    channel = connection.channel()
    if publisher:
        # BlockingConnection 下 confirm_delivery 是 publish-and-wait；生产环境应改 Streaming Confirms
        channel.confirm_delivery()
    return connection, channel


def publish_json(
    channel: pika.channel.Channel,
    *,
    exchange: str,
    routing_key: str,
    payload: dict[str, Any],
    message_id: Optional[str] = None,
    headers: Optional[dict[str, Any]] = None,
    priority: int = 0,
) -> str:
    mid = message_id or str(uuid.uuid4())
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    properties = pika.BasicProperties(
        delivery_mode=pika.DeliveryMode.Persistent,
        content_type="application/json",
        message_id=mid,
        headers=headers or {},
        priority=priority,
    )
    ok = channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=body,
        properties=properties,
        mandatory=False,
    )
    if ok is False:
        print("[!] Publisher confirm nack — 队列可能已满（reject-publish）", file=sys.stderr)
        sys.exit(1)
    return mid


def parse_json(body: bytes) -> dict[str, Any]:
    return json.loads(body.decode("utf-8"))
