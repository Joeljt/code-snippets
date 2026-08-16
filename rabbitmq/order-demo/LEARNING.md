# 渐进式学习路径

完整版 demo 一次塞了 20+ 文件，适合**复习**，不适合**第一次学**。

按下面 8 个阶段顺序来。每个阶段：

- **只有本阶段需要的文件**（通常 2～6 个）
- **独立可运行**，不依赖后面的阶段
- README 里写清：本阶段学什么、读哪几个文件、怎么跑

Broker 共用上一级目录的 Docker（所有阶段连 `localhost:5672`）。

---

## 阶段一览

| 阶段 | 目录 | 新增知识点 | 大约文件数 |
| --- | --- | --- | --- |
| 1 | [`stages/01-hello-order/`](stages/01-hello-order/) | 队列、发消息、收消息、Default Exchange | 2 |
| 2 | [`stages/02-topic-events/`](stages/02-topic-events/) | Topic 交换机、routing key、下单/支付事件 | 4 |
| 3 | [`stages/03-inventory-ack/`](stages/03-inventory-ack/) | Direct 命令、Manual ACK、Prefetch | 5 |
| 4 | [`stages/04-reliability/`](stages/04-reliability/) | Publisher Confirm、持久化、SQLite 状态与幂等 | 6 |
| 5 | [`stages/05-delay-cancel/`](stages/05-delay-cancel/) | 延迟插件、超时关单 | 5 |
| 6 | [`stages/06-dead-letter/`](stages/06-dead-letter/) | DLX、x-delivery-limit、x-death | 5 |
| 7 | [`stages/07-notify-priority/`](stages/07-notify-priority/) | Fanout 广播、优先级队列 | 6 |
| 8 | [`full/`](full/) | 备份交换机、溢出策略、全部 worker 汇合 | 20+ |

---

## 怎么学

1. 启动 Broker（只需一次）：

```bash
cd rabbitmq/order-demo
docker compose up -d --build
```

2. 从 **阶段 1** 开始，进入对应目录，**只读该目录 README 列出的文件**。

3. 跑通本阶段后，再进入下一阶段。不要提前打开 `full/`。

4. 阶段 8 的 `full/` 就是之前的完整 demo（七条演练路径、一键 `start_workers.sh`）。

---

## 和笔记的对照

| 你的笔记 | 最早出现在 |
| --- | --- |
| `rabbitmq/docs/channels.md` | 阶段 4（connection 封装） |
| `rabbitmq/docs/ack-and-confirm.md` | 阶段 3（ACK）→ 阶段 4（Confirm） |
| `rabbitmq/docs/exchanges.md` | 阶段 2（Topic）→ 阶段 8（AE） |
| `rabbitmq/docs/queues.md` | 阶段 4（quorum）→ 阶段 6～8（DLX/优先级/溢出） |
| `rabbitmq/docs/可靠性保证.md` | 阶段 4 串起来 |

---

## 设计原则

- **每阶段增量改动**：新阶段 = 上一阶段代码 + 明确标注的新文件/新参数
- **完整版不删**：`full/` 保留全部能力，作终点参照
- **Streams**：仍计划单独 demo，不在此路径内
