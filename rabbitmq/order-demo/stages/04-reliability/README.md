# 阶段 4：可靠性三件套

## 相对阶段 3 多了什么

- **Publisher Confirm** + **持久化消息**（`connection.py`）
- **仲裁队列** quorum（`topology.py` 的 `x-queue-type`）
- **SQLite** 订单状态 + 消费幂等（`db.py`：先处理成功再 `mark_processed`）

## 要读的文件（6 个，重点 3 个）

1. `connection.py` — confirm + persistent
2. `db.py` — 状态机 + processed_ids
3. `inventory_worker.py` — 幂等 ACK 顺序
4. `topology.py` / `place_order.py` / `pay.py` — 对比阶段 3 的差异

## 运行

同阶段 3；可重复 `pay.py` 同一 order_id 观察幂等。

## 下一阶段

→ [`../05-delay-cancel/`](../05-delay-cancel/) 加延迟关单（需 Docker 延迟插件）
