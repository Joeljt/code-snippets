# 阶段 6：死信

## 相对阶段 5 多了什么

- 库存队列：**DLX** + **`x-delivery-limit=3`**
- `--poison` 故意 `nack(requeue=true)`，重试 3 次后进 `order.dead`
- 读 `x-death` 里的 `reason: delivery_limit`

## 要读的文件（4 个）

1. `topology.py` — DLX 参数
2. `inventory_worker.py` — poison 分支
3. `dead_letter_worker.py` — 打印 x-death
4. `send_deduct.py` — 快速触发（不必跑完整下单）

## 运行

```bash
cd stages/06-dead-letter
python dead_letter_worker.py
python inventory_worker.py --poison
python send_deduct.py
```

**预期：** 3 次 poison fail → DLX 打印 delivery_limit

## 下一阶段

→ [`../07-notify-priority/`](../07-notify-priority/)
