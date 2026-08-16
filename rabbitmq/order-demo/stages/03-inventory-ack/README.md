# 阶段 3：扣库存 + Manual ACK

## 相对阶段 2 多了什么

- **Direct 交换机** `inventory.commands`，routing key `deduct`
- **Manual ACK**：处理完才 `basic_ack`（`auto_ack=False`）
- **Prefetch = 1**：未 ACK 时不推下一条

> 完整版会把「支付事件 → 扣库存命令」拆成独立的 `inventory_bridge` worker；这里为了少一个进程，`pay.py` 直接发两条消息。

## 要读的文件（4 个）

1. `topology.py` — 新增 Direct + `inventory.deduct` 队列
2. `pay.py` — 支付 + 发 deduct 命令（对比阶段 2 多了第二行 publish）
3. `inventory_worker.py` — **重点**：`basic_qos(1)` + `basic_ack`
4. `place_order.py` — 与阶段 2 类似

## 运行

```bash
cd stages/03-inventory-ack
python inventory_worker.py    # 终端 1
python place_order.py
python pay.py <order_id>
```

**预期：** `[inventory] deducting ...` → `[inventory] done ...`

## 下一阶段

阶段 4 加上 **Publisher Confirm、持久化消息、SQLite 订单状态**，开始讲「消息不丢」。

→ [`../04-reliability/`](../04-reliability/)
