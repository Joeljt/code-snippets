#!/usr/bin/env python3
import sys

from connection import open_channel, publish
from db import init_db, mark_paid
from topology import EX_CMD, EX_EVENTS, declare_topology


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python pay.py <order_id>")
    oid = sys.argv[1]
    init_db()
    if not mark_paid(oid):
        print(f"[*] already paid or missing: {oid}")
        return
    conn, ch = open_channel(publisher=True)
    declare_topology(ch)
    publish(ch, EX_EVENTS, "order.paid", oid)
    publish(ch, EX_CMD, "deduct", oid)
    print(f"[x] paid + deduct  {oid}")
    conn.close()


if __name__ == "__main__":
    main()
