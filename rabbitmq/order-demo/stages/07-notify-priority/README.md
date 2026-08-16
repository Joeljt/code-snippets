# 阶段 7：Fanout + 优先级

## 相对阶段 6 多了什么

- **Fanout** `notifications`：发货后广播，SMS 队列收到同一条
- **经典队列优先级** `shipping.jobs`（`x-max-priority=5`，仲裁队列不支持优先级）
- **prefetch=1** 否则优先级失效

## 要读的文件（4 个）

1. `topology.py`
2. `seed_priority.py` — 3×priority=1 + 1×priority=5
3. `shipping_worker.py` — prefetch=1，发完 fanout 通知
4. `notify_sms.py`

## 运行

```bash
cd stages/07-notify-priority
python notify_sms.py              # 终端 1
python seed_priority.py           # 终端 2（先不要开 shipping）
python shipping_worker.py --slow  # 终端 2
```

**预期：** VIP 先于剩余 normal 完成；SMS 收到发货通知

## 下一阶段：完整版

所有机制汇合 + 备份交换机 + 溢出策略 + 10 个 worker：

→ [`../../full/README.md`](../../full/README.md)
