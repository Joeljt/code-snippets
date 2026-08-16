# 电商订单履约 RabbitMQ Demo 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `rabbitmq/order-demo/` 实现可演练的电商履约脚本集，覆盖 spec 中 B 方案全部知识点。

**Architecture:** 多进程 CLI + pika；`topology.py` 幂等声明；SQLite 做状态与幂等；docker-compose 提供带延迟插件的 RabbitMQ 4.0.7。

**Tech Stack:** Python 3.9+, pika, SQLite, Docker Compose, RabbitMQ 4.0.7 + delayed-message-exchange v4.0.7

## Global Constraints

- 目录：`rabbitmq/order-demo/`，不改现有教程
- Python 3.9 + pika，无 Web 框架
- 核心队列 quorum + durable；发货/通知用 classic（优先级必须 classic）
- 所有 publish 进程 `confirm_delivery()`；所有 consume 手动 ACK
- 延迟关单用 `x-delayed-message`，不用单条 expiration TTL
- 验收：README 七条手册路径

---

### Task 1: 基础设施

**Files:** `docker-compose.yml`, `Dockerfile.rabbitmq`, `connection.py`, `topology.py`, `db.py`, `.gitignore`

- [ ] Docker 镜像 pinned 4.0.7 + 插件 v4.0.7
- [ ] `declare_topology(channel)` 声明全部 exchange/queue/binding
- [ ] SQLite 订单/库存/幂等表

### Task 2: 生产者脚本

**Files:** `place_order.py`, `pay.py`, `debug_publish.py`, `seed_shipping_priority.py`, `flood_sms.py`, `flood_inventory.py`

### Task 3: Worker 进程

**Files:** `workers/*.py`（10 个 worker）

### Task 4: 文档与验收

**Files:** `README.md` — 七条演练路径 + 启动说明
