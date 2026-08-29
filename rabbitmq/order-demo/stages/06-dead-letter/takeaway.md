# Stage 6 Takeaway

> 对应代码：[`topology.py`](topology.py) · [`inventory_worker.py`](inventory_worker.py) · [`dead_letter_worker.py`](dead_letter_worker.py) · [`send_deduct.py`](send_deduct.py)

## 整体逻辑

死信是 RabbitMQ **内置**能力（不是 delayed 那种插件）。客户端声明拓扑 + 该 ack/nack；**进 DLX 由 Broker 内部转发**，不用自己往死信交换机 publish。

```
send_deduct → inventory.commands / deduct → inventory.deduct
                                              │
                    nack(requeue) / 未 ack 断连 再投 …
                                              │
                         达到 x-delivery-limit
                                              ▼
                                         order.dlx ──#──► order.dead → dead_letter_worker
```

串起来就是：

1. 声明死信交换机 + 死信队列，并 bind  
2. **在源队列上**配置 `x-dead-letter-exchange`（每个队列各自指定）和可选的 `x-delivery-limit`  
3. 退回再投次数到了（或其它死信条件）→ Broker 把消息发到对应 DLX  
4. 再按交换机类型 + binding 分发：有匹配队列就进死信队列，没有就丢掉  

---

## 拓扑：两套路由别混

```python
ch.queue_declare(
    Q_DEDUCT, durable=True,
    arguments={**QUORUM, "x-dead-letter-exchange": EX_DLX, "x-delivery-limit": 3},
)
ch.queue_bind(Q_DEDUCT, EX_CMD, routing_key="deduct")   # 正常收消息
ch.queue_bind(Q_DEAD, EX_DLX, routing_key="#")          # 死信怎么进 order.dead
```

| | 作用 |
| --- | --- |
| `queue_bind(…, EX_CMD, "deduct")` | **正常路径**：业务 publish 进 `inventory.deduct` |
| `x-dead-letter-exchange` | **异常路径**：出问题时 Broker 发到 `order.dlx`（队列属性，不是 bind） |
| `x-delivery-limit: 3` | quorum：**退回再投**次数上限，到了走死信 |
| `**QUORUM` | Python 字典解包，摊进 `x-queue-type: quorum` |

`x-dead-letter-exchange` **不是**「这个队列从哪个交换机收业务消息」。

DLX 用 Topic + `#`：接住 Broker 死信时带的各种 routing key。单一垃圾桶时 **Fanout + bind 死信队列** 效果等价、往往更干净；本 demo 用 Topic+# 便于以后按 key 拆。交换机 type 一旦 declare 不能改，要换得先删旧的。

死信队列本身不必是 quorum；classic 也能挂 DLX。`x-delivery-limit` 才是 quorum 专用；classic 常用 `nack(requeue=False)` / TTL / 溢出等触发死信。

---

## 什么会计入 delivery limit

会「退回 Ready 再投」、从而推高次数的：

- `basic_nack` / `reject` 且 **`requeue=True`**（`--poison`）  
- consumer **未 ack 就断连/重启**（实测：频繁重启 worker，大约第 4 次进死信，limit=3）

**不算**次数的：只是处理慢、一直占着 Unacked——还是同一次投递。

Broker **没有**自带退避：poison 时会连续快速 requeue + 再投，刷屏很正常。

其它进 DLX 的触发（机制相同）：`requeue=False`、消息 TTL、队列溢出等。

---

## 实测与小坑

```bash
python dead_letter_worker.py
python inventory_worker.py --poison
python send_deduct.py
```

预期：连续若干次 poison fail → `order.dead` 打出 `x-death`（常见 `reason: delivery_limit`）。

- `basic_qos(10)` 错：第一个参数是 `prefetch_size`，Broker 报 `NOT_IMPLEMENTED`；要用 `basic_qos(prefetch_count=10)`  
- `x-death` 里有 `datetime`，`json.dumps` 需 `default=str`

## 下一阶段

Stage 7：Fanout + 优先级（可跳过）→ [`../07-notify-priority/`](../07-notify-priority/)
