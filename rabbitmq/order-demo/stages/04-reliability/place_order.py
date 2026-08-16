#!/usr/bin/env python3
from connection import open_channel, publish
from db import create_order, init_db
from topology import EX_EVENTS, declare_topology


def main():
    init_db()
    oid = create_order()
    conn, ch = open_channel(publisher=True)
    declare_topology(ch)
    publish(ch, EX_EVENTS, "order.created", oid)
    print(f"[x] order.created (persistent+confirm)  {oid}")
    conn.close()


if __name__ == "__main__":
    main()
