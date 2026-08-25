# Stage 3 Takeaway

> 对应代码：[`topology.py`](topology.py) · [`place_order.py`](place_order.py) · [`pay.py`](pay.py) · [`inventory_worker.py`](inventory_worker.py)

## 整体链路

本阶段核心是 **Direct 命令队列** + **prefetch**。publish / consume 流程和 Stage 2 一样，只是换了交换机类型：

```
pay  ──deduct──►  inventory.commands (Direct)  ──deduct──►  inventory.deduct  ──►  inventory_worker
```

```python
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=Q_INVENTORY_DEDUCT, on_message_callback=on_message, auto_ack=False)
```

Direct：`publish routing_key` **完全等于** binding 的 routing key 才进队。Topic 若绑的是不含 `*`/`#` 的固定 key（比如 `order.paid`），路由效果几乎一样——机制没变，还是「向交换机发指定 routing_key → binding 匹配 → 队列 → consumer」。

---

## pay 发了两条，Stage 3 只消费一条

```python
channel.basic_publish(exchange=EX_ORDER_EVENTS, routing_key="order.paid", ...)       # 事件
channel.basic_publish(exchange=EX_INVENTORY_COMMANDS, routing_key="deduct", ...)  # 命令 ← 本阶段重点
```

Stage 3 **没有**给 `order.events` 绑队列。若 Broker 上还留着 Stage 2 的 `order.events.log` + binding，事件会进那个遗留队列变成 Ready；本阶段 worker 不管它。deduct 那条才是 `inventory_worker` 在消费。

---

## Prefetch、轮询、背压

三者别混：

| | 管什么 |
| --- | --- |
| **轮询** | 同一队列多个 consumer 时，下一条 Ready **优先轮着给谁** |
| **Prefetch** | 某个 consumer **未 ack 槽位**最多 `N` 条；满了 Broker 就先别再 deliver 给它 |
| **背压（这里）** | consumer 用槽位余量限制 **Broker → Consumer** 的推送节奏，不是去喊业务 Publisher 停手 |

### Prefetch = 固定大小的滑动窗口

```
业务 Publisher ──publish──► 队列 Ready ──deliver──► Consumer
                              ▲                │
                              │                │ 槽位 Unacked ≤ N
                         槽满照样能进队         │
                         Publisher 通常无感     ack → 还 1 格 → 再 deliver
```

- `N` 用 `basic_qos` **事前配好**
- deliver 占一格，**ack 还一格**，Broker 才能再推——节奏跟着 ack 走
- 槽满了：**Broker** 知道不能再给这个 consumer 推；**不是** `basic_publish` 的应用自动停发
- 窗口一般不会按负载自动变大变小（要自己改 qos）

和 TCP 接收窗口类似：都是 **接收方限制发送方还能再推多少**。这里的「发送方」是 Broker（deliver），不是业务 Publisher。MQ 中间有队列接住积压，所以很少让 consumer 直接通知 Publisher 减速；实践里更多是队列缓冲 + prefetch + 扩容 / 限长。

不设 prefetch 时：**manual ack alone 挡不住** Broker 一口气 deliver 很多条 → Unacked 飙高，正文已经进到消费端缓冲。`prefetch=1` 就是卡住这件事。

单 consumer 也能测：停 worker → 连发几条 deduct → 再起 worker（有 `sleep`）。`prefetch=1` 时 Unacked ≈ 1，其余 Ready；不设则可能一下全变 Unacked。

多 consumer：谁槽位还没满，谁还能接着领。两个都满了，才一起 Ready 等。

---

## Deliver 之后消息在哪？

```
Ready  ──deliver──►  Unacked  ──basic_ack──►  从队列删除
                         │
                         └── 断连 / 未 ack → 可回 Ready 重投
```

Deliver **不只是改状态**：

- **队列里**：还在，变成 Unacked，名花有主，不会再派给别人
- **consumer 进程里**：正文已经通过网络收到（TCP / pika 缓冲）

所以是「两边都有」。ack 之前 Broker 不放手，consumer 挂了还能重投。

单线程回调时：同一时刻通常只有一条在跑 `on_message`。`Unacked > 1` 时，其余已经在消费端里排队等回调——这是 **进程本地排队**，不是队列的 Ready。

---

## 本阶段命令

```bash
python inventory_worker.py    # 终端 1
python place_order.py
python pay.py <order_id>
```

测 prefetch：停 worker → 多 pay 几次 → 再起 worker，看 `inventory.deduct` 的 Ready / Unacked。

## 下一阶段

Stage 4：Publisher Confirm、消息持久化、订单状态 → [`../04-reliability/`](../04-reliability/)
