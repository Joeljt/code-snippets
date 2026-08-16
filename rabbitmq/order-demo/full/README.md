# 阶段 8：完整版电商履约 Demo

前 7 个阶段见 [`../LEARNING.md`](../LEARNING.md)。这里是**全部机制汇合**的版本。

把 Topic / Direct / Fanout、延迟关单、死信、优先级、溢出、Publisher Confirm、Manual ACK 串成一条可演练的下单链路。

设计文档：[`docs/superpowers/specs/2026-08-15-order-demo-design.md`](../../../docs/superpowers/specs/2026-08-15-order-demo-design.md)

> 单节点 quorum 仅供学习参数声明；生产环境至少 3 节点集群。

## 0. 启动 Broker

在 **`rabbitmq/order-demo`**（上一级）：

```bash
docker compose up -d --build
```

## 1. 安装依赖

仓库根目录：`uv sync`

## 2. 常驻 Worker

在 **`full/`** 目录：

```bash
./start_workers.sh
```

- 日志：`logs/<name>.log`，当前终端 `tail -F` 合并显示
- 另开终端触发：`python place_order.py && python pay.py <order_id>`

`Ctrl+C` 或 `./stop_workers.sh` 停止。

## 3. 七条演练路径

（命令均在 `full/` 下执行）

### 路径 1：快乐路径

```bash
python place_order.py
python pay.py <order_id>
```

预期：`inventory.deducted`、`shipped + notify`、三端通知、`timeout skipped`

### 路径 2：超时关单

只 `place_order.py`，不 pay → 约 15 秒 `order.cancelled (timeout)`

### 路径 3：VIP 插队

```bash
python seed_shipping_priority.py
python workers/shipping_worker.py --slow
```

### 路径 4：毒消息死信

```bash
python workers/inventory_worker.py --poison
python place_order.py && python pay.py <order_id>
```

### 路径 5：备份交换机

```bash
python place_order.py --bad-key
```

### 路径 6 / 7：溢出

见原手册：`flood_sms.py`、`flood_inventory.py`（先停对应 worker）

## 4. 清理

```bash
cd .. && docker compose down -v
rm -f order-demo.sqlite logs/*
```
