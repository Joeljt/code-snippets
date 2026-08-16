# 阶段 2：Topic 事件

## 相对阶段 1 多了什么

- **Topic 交换机** `order.events`
- routing key：`order.created`、`order.paid`
- 消费者用 `order.#` 绑定，一条队列收所有订单事件

## 要读的文件（4 个）

1. `topology.py` — 声明 Topic 交换机
2. `place_order.py` — 发 `order.created`
3. `pay.py` — 发 `order.paid`
4. `event_worker.py` — 绑定 `order.#` 并打印

## 运行

```bash
cd stages/02-topic-events
python event_worker.py          # 终端 1
python place_order.py           # 终端 2 → 看到 created
python pay.py <order_id>        # 终端 2 → 看到 paid
```

## 下一阶段

阶段 3 增加 **Direct 命令队列** 扣库存，并引入 **Manual ACK + Prefetch**。

→ [`../03-inventory-ack/`](../03-inventory-ack/)
