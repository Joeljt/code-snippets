# Stage 4 Takeaway

> 对应代码：[`connection.py`](connection.py) · [`db.py`](db.py) · [`topology.py`](topology.py) · [`place_order.py`](place_order.py) · [`pay.py`](pay.py) · [`inventory_worker.py`](inventory_worker.py)

## 整体链路

本阶段在 Stage 3 的 deduct 链路上加 **可靠性三件套**：Publisher Confirm、消息 Persistent、quorum 队列，再加上 **SQLite 幂等**。

```
place_order → DB 建单(unpaid) → publish order.created（本 stage 基本没人收）

pay → mark_paid(unpaid→paid) 成功才继续
        ├─ order.events / order.paid   ← 壳子，Stage 4 无 bind
        └─ inventory.commands / deduct → inventory.deduct(quorum) → inventory_worker
              ├─ message_id 已处理 → 直接 ack
              └─ 业务处理 → mark_processed → ack
```

`order.events` 仍 declare + publish，是完整版事件总线的形状；**本 stage 真正要盯的是 deduct 命令队列**。没 bind 时消息被丢掉（或被 Stage 2 遗留的 `order.events.log` 捡走）。

---

## Publisher Confirm（协议，不是纯业务逻辑）

和 consumer `basic_ack` **对称、方向相反**：

| | 谁通知谁 | 表示什么 |
| --- | --- | --- |
| Consumer ack | Consumer → Broker | 处理完了，可从队列删 |
| Publisher Confirm | Broker → Publisher | Broker **收下了**这条消息 |

藏在 [`connection.py`](connection.py)：

```python
ch.confirm_delivery()   # 打开 confirm；BlockingConnection 下 publish-and-wait
ok = channel.basic_publish(...)
if ok is False:         # Broker nack
    ...
```

Confirm 确认的是：**Broker 已接受并路由进匹配队列**（持久化消息通常还要满足落盘策略）。  
**不表示** consumer 已处理。后面 Ready / Unacked 仍是 Broker ↔ Consumer。

正常跑通时往往看不到日志——`ok` 为真就静默继续。想观察：成功时打一行 confirmed，或停掉 Broker 再 publish。

---

## Persistent：消息活过重启

Stage 1 实测：队列 durable → 重启队列还在，**消息没了**（没设 Persistent）。

要消息也活过重启，通常两样齐：

| | 作用 |
| --- | --- |
| 队列 durable / quorum | 队列元数据（及 quorum 副本）还在 |
| 消息 `delivery_mode=Persistent` | 消息内容按队列类型写入磁盘 |

实测（注释掉 worker `basic_ack` → pay → Unacked → `docker compose restart`）：

1. 重启后消息还在，worker 上线前是 **Ready**
2. worker 再上线 → 再次 deliver → **Unacked**
3. 同一条可能被投递第二次 → 所以要幂等

磁盘上**不是**按 order_id 存的可读文件。本 demo 数据在容器 `/var/lib/rabbitmq`（卷 `rabbitmq-data`）。Stage 4 的 quorum 队列走 Raft：

```text
.../mnesia/<node>/quorum/
  ├── *.wal           # 预写日志
  └── <队列子目录>/
        ├── *.segment
        └── snapshots / checkpoints
```

经典 durable 队列则在 `msg_stores` 一类目录。都是 Broker 内部二进制格式。

路径可查：`docker compose exec rabbitmq rabbitmq-diagnostics directories`

---

## Quorum（仲裁队列）到底多了什么

单机 Docker 里「重启 Broker、消息还在」——**classic + durable + Persistent 也能做到**。Confirm、幂等也和是不是 quorum 无关。

| | Classic durable + Persistent | Quorum |
| --- | --- | --- |
| 单机重启丢不丢消息 | 可以不丢 | 可以不丢 |
| **多节点里某个节点挂了** | 队列若只在该节点，可能不可用 | Raft **副本 + 多数派**，还能继续服务 |
| 设计目标 | 单队列持久化 | **复制 + 共识**（现代可靠队列默认推荐） |

不是「消息只在 A，A 挂了再转发到 B/C」，而是：

```
publish（confirm）→ 写入 quorum 多数派副本（A/B/C 里够票的那些）
A 挂了 → 选新 leader（如 B）→ 用 B 上已有副本继续服务
consumer 若连的是挂掉的 A，需要重连到其他节点
```

本 demo 只有一个节点，**复制 / 故障转移看不出来**；你看到的存活主要来自落盘。Stage 4 写成 quorum，是对齐完整版/生产推荐，和 confirm、Persistent、幂等凑成可靠性一课。

一句话：**消息重启还在 ≈ 持久化；节点挂了队列还能在别的节点接着跑 ≈ quorum（要集群才明显）。**

---

## 幂等：定义 vs 实现

**定义**：同一操作做一次和做 N 次，对外结果一样（不重复扣库存、状态不乱跳）。

**前置检查 / 条件更新** 只是常见手法，用来达到这个性质：

| 位置 | 防的是什么 |
| --- | --- |
| `pay` 里 `mark_paid(... AND status='unpaid')` | 同一订单别再发第二遍 deduct（发之前挡） |
| `worker` 里 `is_processed(message_id)` | 消息进队后被 **重投**（至少一次），别处理第二次 |

只靠 pay 挡不住 Broker 重投；只靠 worker 则重复支付仍可能多发几条（最终被幂等吃掉）。两边互补。

第二次可以早退（直接 ack return）；早退后的系统状态仍应和「只成功处理一次」一样。

---

## 复习：Exchange / Queue / Bind（顺带）

declare 的 exchange 和 queue **在 bind 前没有关系**。bind 把「队列名 + 交换机名 + routing key（binding key）」绑在一起；exchange type 决定怎么用 publish 带来的 routing key 去匹配：

- **Direct**：完全相等才进队  
- **Topic**：`*` / `#` 模式匹配  
- **Fanout**：基本忽略 key，绑了的队列全收  

Publisher 只面对 **exchange + routing key**；Consumer 订阅的是 **队列**。

---

## 本阶段命令

```bash
python inventory_worker.py
python place_order.py
python pay.py <order_id>
# 可重复 pay 同一 order_id，观察 mark_paid / worker 幂等
```

测持久化：注释 worker ack → pay → 看 Unacked → 重启 Broker → 应为 Ready → 再起 worker → Unacked。

## 下一阶段

Stage 5：延迟关单 → [`../05-delay-cancel/`](../05-delay-cancel/)
