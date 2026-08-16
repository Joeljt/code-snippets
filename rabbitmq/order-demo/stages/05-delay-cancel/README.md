# 阶段 5：延迟关单

## 相对阶段 4 多了什么

- **`x-delayed-message` 插件**交换机 `order.delay`
- 下单时发带 `headers.x-delay` 的消息（默认 15 秒）
- `timeout_worker`：仍为 `unpaid` 则关单

## 要读的文件（5 个）

1. `topology.py` — 延迟交换机 + `order.timeout` 队列
2. `place_order.py` — 发延迟消息（对比阶段 4 多一次 publish）
3. `timeout_worker.py` — 到期检查 SQLite 状态
4. `db.py` — `mark_cancelled`

## 运行

```bash
cd stages/05-delay-cancel
python timeout_worker.py
python place_order.py
# 不 pay，等 15 秒 → cancelled
```

## 下一阶段

→ [`../06-dead-letter/`](../06-dead-letter/)
