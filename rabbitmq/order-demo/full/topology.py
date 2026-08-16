"""幂等声明 demo 全部交换机、队列与绑定。"""

from __future__ import annotations

import pika
from pika.exchange_type import ExchangeType

# --- 交换机 ---
EX_ORDER_EVENTS = "order.events"
EX_ORDER_DELAY = "order.delay"
EX_INVENTORY_COMMANDS = "inventory.commands"
EX_NOTIFICATIONS = "notifications"
EX_UNROUTABLE_AE = "unroutable.ae"
EX_ORDER_DLX = "order.dlx"

# --- 队列 ---
Q_TIMEOUT = "order.timeout"
Q_INVENTORY_BRIDGE = "inventory.bridge"
Q_INVENTORY_DEDUCT = "inventory.deduct"
Q_INVENTORY_RESTORE = "inventory.restore"
Q_SHIPPING_JOBS = "shipping.jobs"
Q_NOTIFY_SMS = "notify.sms"
Q_NOTIFY_EMAIL = "notify.email"
Q_NOTIFY_APP = "notify.app"
Q_ORDER_DEAD = "order.dead"
Q_AUDIT_UNROUTABLE = "audit.unroutable"

QUORUM = {"x-queue-type": "quorum"}


def declare_topology(channel: pika.channel.Channel) -> None:
    # 备份交换机必须先于带 AE 的主交换机声明
    channel.exchange_declare(
        exchange=EX_UNROUTABLE_AE,
        exchange_type=ExchangeType.fanout,
        durable=True,
    )
    channel.exchange_declare(
        exchange=EX_ORDER_EVENTS,
        exchange_type=ExchangeType.topic,
        durable=True,
        arguments={"alternate-exchange": EX_UNROUTABLE_AE},
    )
    # 延迟插件：关单用 x-delay header，不用单条 expiration（避免队头阻塞）
    channel.exchange_declare(
        exchange=EX_ORDER_DELAY,
        exchange_type="x-delayed-message",
        durable=True,
        arguments={"x-delayed-type": "direct"},
    )
    channel.exchange_declare(
        exchange=EX_INVENTORY_COMMANDS,
        exchange_type=ExchangeType.direct,
        durable=True,
    )
    channel.exchange_declare(
        exchange=EX_NOTIFICATIONS,
        exchange_type=ExchangeType.fanout,
        durable=True,
    )
    channel.exchange_declare(
        exchange=EX_ORDER_DLX,
        exchange_type=ExchangeType.topic,
        durable=True,
    )

    # --- 队列 ---
    channel.queue_declare(queue=Q_TIMEOUT, durable=True, arguments=QUORUM.copy())
    channel.queue_declare(queue=Q_INVENTORY_BRIDGE, durable=True, arguments=QUORUM.copy())

    # 核心库存：仲裁 + DLX + delivery-limit + reject-publish 溢出
    channel.queue_declare(
        queue=Q_INVENTORY_DEDUCT,
        durable=True,
        arguments={
            **QUORUM,
            "x-dead-letter-exchange": EX_ORDER_DLX,
            "x-delivery-limit": 3,
            "x-max-length": 5,
            "x-overflow": "reject-publish",
        },
    )
    channel.queue_declare(
        queue=Q_INVENTORY_RESTORE,
        durable=True,
        arguments={
            **QUORUM,
            "x-dead-letter-exchange": EX_ORDER_DLX,
            "x-delivery-limit": 3,
        },
    )

    # 优先级必须用 classic（仲裁队列不支持 x-max-priority）
    channel.queue_declare(
        queue=Q_SHIPPING_JOBS,
        durable=True,
        arguments={"x-max-priority": 5},
    )

    channel.queue_declare(
        queue=Q_NOTIFY_SMS,
        durable=True,
        arguments={
            "x-max-length": 5,
            "x-overflow": "drop-head",
            "x-dead-letter-exchange": EX_ORDER_DLX,
        },
    )
    channel.queue_declare(queue=Q_NOTIFY_EMAIL, durable=True)
    channel.queue_declare(queue=Q_NOTIFY_APP, durable=True)
    channel.queue_declare(queue=Q_ORDER_DEAD, durable=True, arguments=QUORUM.copy())
    channel.queue_declare(queue=Q_AUDIT_UNROUTABLE, durable=True)

    # --- 绑定 ---
    channel.queue_bind(queue=Q_TIMEOUT, exchange=EX_ORDER_DELAY, routing_key="order.timeout")
    channel.queue_bind(queue=Q_INVENTORY_BRIDGE, exchange=EX_ORDER_EVENTS, routing_key="order.paid")
    channel.queue_bind(queue=Q_INVENTORY_BRIDGE, exchange=EX_ORDER_EVENTS, routing_key="order.cancelled")
    channel.queue_bind(queue=Q_INVENTORY_DEDUCT, exchange=EX_INVENTORY_COMMANDS, routing_key="deduct")
    channel.queue_bind(queue=Q_INVENTORY_RESTORE, exchange=EX_INVENTORY_COMMANDS, routing_key="restore")
    channel.queue_bind(queue=Q_SHIPPING_JOBS, exchange=EX_ORDER_EVENTS, routing_key="inventory.deducted")
    channel.queue_bind(queue=Q_NOTIFY_SMS, exchange=EX_NOTIFICATIONS)
    channel.queue_bind(queue=Q_NOTIFY_EMAIL, exchange=EX_NOTIFICATIONS)
    channel.queue_bind(queue=Q_NOTIFY_APP, exchange=EX_NOTIFICATIONS)
    channel.queue_bind(queue=Q_ORDER_DEAD, exchange=EX_ORDER_DLX, routing_key="#")
    channel.queue_bind(queue=Q_AUDIT_UNROUTABLE, exchange=EX_UNROUTABLE_AE)


if __name__ == "__main__":
    from connection import open_channel

    conn, ch = open_channel()
    declare_topology(ch)
    print("[*] Topology declared.")
    conn.close()
