#!/usr/bin/env python3
from connection import BROKER, DELAY_MS, pub
from db import create_order, init_db
from topology import EX_DELAY, EX_EVENTS, declare_topology
import pika


def main():
    init_db()
    oid = create_order()
    conn = pika.BlockingConnection(BROKER)
    ch = conn.channel()
    ch.confirm_delivery()
    declare_topology(ch)
    pub(ch, EX_EVENTS, "order.created", oid)
    pub(ch, EX_DELAY, "order.timeout", oid, headers={"x-delay": DELAY_MS})
    print(f"[x] created {oid}, timeout in {DELAY_MS}ms if unpaid")
    conn.close()


if __name__ == "__main__":
    main()
