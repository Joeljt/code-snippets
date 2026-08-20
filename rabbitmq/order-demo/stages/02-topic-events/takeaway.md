# Stage 2 Takeaway

> 对应代码：[`topology.py`](topology.py) · [`place_order.py`](place_order.py) · [`pay.py`](pay.py) · [`event_worker.py`](event_worker.py)

## 整体链路

Stage 1 看起来像「发送端直接进队列」，Stage 2 拆开了中间这层：

```
发送端 ──publish──► 交换机 ──binding──► 队列 ──consume──► 消费端
```

发送端和队列之间**没有绑定关系**，二者通过交换机发生联系。发送端只面对 Exchange + routing key；进哪个队列由**交换机类型 + binding** 决定。

```
place_order / pay  ──►  order.events (Topic)  ──order.#──►  order.events.log  ──►  event_worker
```

Broker = RabbitMQ 服务本身（Docker 里那个容器）。消息、队列都在 Broker 里；**Exchange 不存消息**，管理台看 Ready / Unacked 要去 **Queues** 页。

管理台别认错名字：

- **`order.events`** — 交换机（不是队列）
- **`order.events.log`** — Stage 2 的队列
- **`order.created`** — Stage 1 遗留的队列；Stage 2 的 publish **不会**进这里

---

## Topic 与 binding

Stage 2 用 Topic 交换机 `order.events`，routing key 是事件名：`order.created`、`order.paid`。

交换机是转发消息到队列的**中间人**：通过 routing key 匹配 binding，把命中的消息转发到自己绑定的队列。队列叫什么、后面 consumer 怎么处理，都和交换机无关。

```python
# 发送端：declare 交换机 + publish（不声明队列）
channel.basic_publish(
    exchange=EX_ORDER_EVENTS,
    routing_key="order.created",   # 不必等于队列名
    body=order_id.encode(),
)

# 消费端：建队列 + bind + consume
channel.queue_declare(queue="order.events.log", durable=True)
channel.queue_bind(queue="order.events.log", exchange=EX_ORDER_EVENTS, routing_key="order.#")
channel.basic_consume(queue="order.events.log", on_message_callback=on_message, auto_ack=False)
```

Topic 用 `order.#` 匹配 `order.created`、`order.paid`（`*` 一词，`#` 多词）。路由规则由**交换机类型**决定，不是「默认必须 routing key == 队列名」：

- **Direct**：`publish routing_key == binding routing_key` 就定向投递，**队列名无所谓**
- **Topic**：模式匹配（本 stage）
- **Fanout**：忽略 routing key，绑定的队列全收（后面阶段）

Stage 1 的 Default Exchange = 隐式 Direct，且 Broker **自动**做了 `binding routing_key = queue name`，所以看起来像必须同名。Default 只是省略了 bind，实际上是 `publish rk == binding rk == queue name` 这三者叠在一起。

---

## 谁 declare 什么

发送端、消费端都会 `exchange_declare`，和 Stage 1 两边都 `queue_declare` 一样，是**幂等和兜底**。

只有消费端 `queue_declare` + `queue_bind`，因为**要收消息的一方**决定关心哪些 routing key。发送端直接面向交换机，不声明队列。

| 发送端 | 消费端 |
| --- | --- |
| `exchange_declare` | `exchange_declare` + `queue_declare` + `queue_bind` + `basic_consume` |

**从没跑过 event_worker（没有 binding）：** publish 到 `order.events` 后**匹配不到队列，消息直接丢**，Queues 里看不到。

**binding 已建好、consumer 暂时离线（实测）：** `place_order` / `pay` 会进 `order.events.log`，全部 **Ready** 积压；consumer 上线 + 正常 ack 会消费完。注释 ack 则转 **Unacked** 积压，逻辑同 [Stage 1 takeaway](../01-hello-order/takeaway.md#ready--unacked)。

---

## binding 改代码不会改 Broker

`queue_bind` 是**往 Broker 上追加**，不会删掉旧的。

实测：binding 从 `order.#` 改成 `order.paid` 后，`place_order` 仍能收到——旧的 **`order.#` 还在 Broker 上**。改代码里的 routing_key ≠ 改 Broker 拓扑。管理台 **Queues → Bindings** 可验证。

干净重测：删队列再起 worker，或先 `queue_unbind` 再 bind。

```bash
docker compose exec rabbitmq rabbitmqctl delete_queue order.events.log
```

---

## 每个队列自带的 Default binding

管理台 **Bindings (2)** 里那条 `(Default exchange binding)` 不是 Stage 1 遗留。

**每个队列**都会自动以 Direct 方式，接收 `routing_key == 自己队列名` 的 Default Exchange 消息——不用手写 bind。不管还绑了哪些交换机，这条路径**永远存在**，和其他 binding **并行**：

```
Default ("")  --rk=order.events.log-->  order.events.log
order.events  --order.# / order.paid-->  order.events.log
```

不会因此误收 `order.created`；除非有人 `exchange=""` 且 `routing_key="order.events.log"` 直发。

---

## 管理台小坑

- worker 在线 + 立刻 ack：消息太快，**Queued messages** 常是 0，**Message rates** 能看到 publish / ack
- 想眼看 Ready：停 worker → publish → 再看 `order.events.log`
- Stage 1 当时能看到波动，多半是积压实验或旧消息；正常 ack 快路径下 Stage 1 也多半只有 rates 在动

---

## 本阶段命令

```bash
python event_worker.py          # 终端 1
python place_order.py           # 终端 2
python pay.py <order_id>
```

## 下一阶段

Stage 3：**Direct** 命令队列 + Prefetch → [`../03-inventory-ack/`](../03-inventory-ack/)
