# 阶段 1：Hello Order

## 本阶段学什么

- 生产者 `basic_publish`、消费者 `basic_consume`
- **Default Exchange**（`exchange=""`）：routing key = 队列名，消息直达队列
- 队列声明 `queue_declare`

## 要读的文件（仅 2 个）

1. `place_order.py` — 发一条订单号
2. `log_worker.py` — 收并打印

## 运行

终端 1（在 `rabbitmq/order-demo` 先 `docker compose up -d`）：

```bash
cd stages/01-hello-order
python log_worker.py
```

终端 2：

```bash
python place_order.py
```

**预期：** 终端 1 出现 `[order] received ord_xxxxxxxx`

## 下一阶段

阶段 2 会把「一条队列」换成 **Topic 交换机**，用 routing key 区分 `order.created` / `order.paid`。

→ [`../02-topic-events/`](../02-topic-events/)
