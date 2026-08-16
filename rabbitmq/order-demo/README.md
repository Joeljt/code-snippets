# RabbitMQ 订单 Demo

**第一次学请从这里开始 → [`LEARNING.md`](LEARNING.md)**

## 目录结构

```
order-demo/
  LEARNING.md          ← 渐进式学习路径（阶段 1～8）
  docker-compose.yml   ← 共用 Broker（含延迟插件）
  stages/
    01-hello-order/    ← 2 个文件：发/收
    02-topic-events/
    ...
    07-notify-priority/
  full/                ← 阶段 8：完整版（原一次性 demo）
```

## 快速开始

```bash
cd rabbitmq/order-demo
docker compose up -d --build
cd stages/01-hello-order
# 按该目录 README 操作
```

完整版演练见 [`full/README.md`](full/README.md)。

## 设计文档

[`docs/superpowers/specs/2026-08-15-order-demo-design.md`](../../docs/superpowers/specs/2026-08-15-order-demo-design.md)
