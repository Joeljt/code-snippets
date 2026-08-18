# Stage 1 Takeaway

> 对应代码：[`place_order.py`](place_order.py) · [`log_worker.py`](log_worker.py)

## 整体链路

一个最基础的 RabbitMQ 代码模板大概是这样的：

```
Connection（一条 TCP）
  └── Channel（轻量管道）
        ├── queue_declare   声明队列
        ├── basic_publish   发送端投递
        └── basic_consume   消费端订阅 + 回调
```

```
Publisher  ──►  [ Default Exchange ]  ──►  order.created 队列  ──►  Consumer 回调
  (place_order)      exchange=""              Ready / Unacked         (log_worker)
                              ▲
                              │  消息、队列都在 Broker 里
                              │  Broker = RabbitMQ 服务本身（本 demo 里就是 Docker 跑的那个容器）
```

---

## Connection 与 Channel

Channel 是解决高吞吐量问题的解决方案，为了节省 TCP 链接的开销，channel 是一次 TCP 链接内部开启的低成本通信管道，不同 channel 共用一个 TCP 链接，也就是这个 connection。有点类似一个进程里开多个线程的概念，但是 channel 之间也有一些数据交互的注意点，类似线程安全的问题，但是前期可以先不考虑。

```python
connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()
# ... 后续操作都在 channel 上进行
connection.close()
```

---

## 队列声明与 durable

之后就是在 channel 上定义一个队列，发送端就通过把消息投递到这个队列上。同时可以将队列声明为 durable，这个队列的配置等元数据就会持久化到磁盘上，broker 重启队列的数据和配置等也不会丢失。但队列里的消息和这个字段无关，需要单独配置 delivery mode 才行，但是 stage 1 先不考虑。

```python
ORDER_QUEUE = "order.created"

channel.queue_declare(queue=ORDER_QUEUE, durable=True)
```

| 配置 | Stage 1 | 作用 |
| --- | --- | --- |
| 队列 `durable=True` | ✅ 有 | Broker 重启后**队列还在** |
| 消息 `delivery_mode=2` | ❌ 无 | Broker 重启后**消息在不在**（阶段 4 再学） |

---

## 发送消息

之后发送消息的时候调用 `basic_publish` 方法进行消息的发送，stage 1 还没有引入 publisher confirm 的机制，也没有引入交换机，所以就用系统默认的交换机进行转发。

```python
# fire and forget，未启用 publisher confirm
channel.basic_publish(
    exchange="",                    # Default Exchange
    routing_key=ORDER_QUEUE,        # routing key = 队列名 → 直达队列
    body=order_id.encode(),
)
```

如果有交换机的话（stage 2 起），publisher 把消息发给 exchange，exchange 再按派发策略决定怎么路由到具体的队列——direct 直接发，fanout 广播，topic 按照 routing key 来匹配等等，可以是完全匹配或者 `#`/`*` 的通配符匹配逻辑。

---

## 消费端

消费端通过 `basic_consume` 监听队列，有消息时 Broker 推给消费端，在回调函数里处理。

- **`basic_consume(queue=...)`** 才是真正有价值的：指定订阅哪个队列的消息。
- **`queue_declare`** 只是确保 Broker 上有这个队列；已经有了的话，重复声明参数相同也不会有副作用。
- 理论上发送端先启动、队列已在 Broker 上时，消费端**可以不二次声明**，只写 `basic_consume` 完全没问题。Stage 1 两边都写 `queue_declare`，是为了先起 consumer 或单独跑一个脚本时也能跑通。

RabbitMQ 靠**队列名**唯一确定一个队列；发送端和消费端必须读写**同一个队列名**，流程才串得起来（Stage 1 里都是 `order.created`）。最开始说的「consume 同名队列」就是这个意思——别和 `queue_declare` 混为一谈：前者是订阅，后者是建队兜底。

```python
ORDER_QUEUE = "order.created"

channel.queue_declare(queue=ORDER_QUEUE, durable=True)   # 可选：确保队列在

def on_message(channel, method, _properties, body):
    print(f"[order] received {body.decode()}")
    channel.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue=ORDER_QUEUE, on_message_callback=on_message, auto_ack=False)
channel.start_consuming()
```

同时要看消费端的 ack 机制：

| | auto ack | manual ack（Stage 1） |
| --- | --- | --- |
| 行为 | 推给消费者就从队列移除 | 消费者 `basic_ack` 后才移除 |
| 风险 | 业务没处理完也可能丢 | 处理完再确认，更安全 |
| Stage 1 | 未使用 | `auto_ack=False` + 回调里 ack |

- 如果是 **auto ack**，队列把消息转给消费端就会将其从队列中移除，不管消费端是否真正处理完了相关业务
- 如果是 **manual ack**，就需要在业务处理完成以后手动调用 `basic_ack` 进行确认，然后队列收到 ack 以后才会把消息从队列中移除

---

## Ready / Unacked

在 RabbitMQ 的机制下，发送到队列的消息默认是 ready 状态，转发到消费端以后会变成 unacked 状态，等处理完成 `basic_ack` 确认以后会从队列中移除该消息。

```
                         ┌─────────────────────────────────────────┐
                         │              Broker 队列                 │
                         └─────────────────────────────────────────┘

  place_order                有 consumer 订阅              basic_ack
  basic_publish                  deliver                 处理成功
       │                           │                        │
       ▼                           ▼                        ▼
  ┌─────────┐   deliver    ┌───────────┐   basic_ack   ┌─────────┐
  │  Ready  │ ──────────► │  Unacked  │ ────────────► │  删除   │
  │ (等待投递)│             │ (已投递未确认)│             │ (出队)  │
  └─────────┘             └───────────┘             └─────────┘
       ▲                           │
       │                           │ consumer 还在、业务慢
       │         requeue           │ → 一直停在 Unacked
       │      (断连 / 未 ack)       │
       └───────────────────────────┘
                 consumer 挂掉
              （Ctrl+C、崩溃、Channel 关闭）

  回滚到 Ready 后，等新 consumer 上线 → 再次 deliver → 又回到 Unacked
  （同一条消息可能被重复投递 —— 阶段 4 会学幂等）
```

如果业务处理异常，或者消费端挂了导致 ack 没有被调用，那消息就会阻塞在队列中等待处理。如果是耗时长，则会保持 unacked 状态；如果是挂掉了，则会回滚到 ready 状态，等待消费端上线后重新派发。

> 管理台看队列 `order.created` 的 Ready / Unacked 计数，是对这段流程最直观的验证方式。

---

## 消息与 Broker 生命周期

这些消息在没有配置的情况下，默认是在内存里的，和 broker 同生命周期，是队列的数据，可以通过配置持久化到磁盘上，这样 broker down 掉再重启，消息不会丢。但是如果没有声明持久化的话，broker 重启消息就会丢掉。消息持久化的配置当前 stage 也不考虑，可以暂时忽略，后面会涉及到。

**Stage 1 实测（`docker compose restart`）：**

- 队列 `order.created` 还在（durable）
- Ready 里的消息没了（未设 persistent）

---

## 本阶段命令

```bash
# 终端 1
python log_worker.py

# 终端 2
python place_order.py
```

## 下一阶段

Stage 2 引入 **Topic Exchange**，用 routing key 区分 `order.created` / `order.paid` → [`../02-topic-events/`](../02-topic-events/)
