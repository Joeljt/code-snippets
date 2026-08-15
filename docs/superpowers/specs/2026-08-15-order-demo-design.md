# 电商订单履约 RabbitMQ Demo 设计

日期：2026-08-15  
范围：`rabbitmq/order-demo/`（不改现有教程脚本）  
后续独立项目：Streams 回放 demo（本文不覆盖）

## 1. 目标

用一条砍瘦的电商履约链路，把已经学过的 **生产核心 + 常见进阶** RabbitMQ 知识点串成可运行、可演练的脚本集。重点是学习，不是拓扑最简。

成功标准：按手册把 7 条路径跑通，并能对照 `rabbitmq/docs/` 说出每个交换机、队列参数、ACK/Confirm 出现的原因。

## 2. 非目标

- Streams / Super Streams / Stream Filtering（下一个独立 demo）
- Exchange-to-Exchange 绑定（笔记里「知道即可」，本 demo 不实现）
- 购物车、SKU 体系、优惠券、真实支付渠道
- Web / HTTP API
- 多节点仲裁集群（单节点 quorum 仅用于声明方式和参数学习）
- 以 pytest 覆盖全部路径的自动化套件（验收是手册演练）

## 3. 知识点映射

| 知识点 | 在 demo 里落在哪 |
| --- | --- |
| Topic | `order.events`：领域事件按 routing key 分流 |
| Direct | `inventory.commands`：`deduct` / `restore` 精确命令 |
| Fanout | `notifications`：短信 / 邮件 / App 各一份 |
| 备份交换机 AE | `order.events` 声明 `alternate-exchange=unroutable.ae` |
| 延迟插件 | `order.delay`（`x-delayed-message`），未支付约 15 秒后关单 |
| Default Exchange | `debug_publish.py` 往 `exchange=""`、`routing_key=队列名` 发一条，仅作对照 |
| 仲裁队列 | 超时、库存、死信、bridge 等核心队列 |
| 经典持久化队列 | 三条通知队列、审计队列；发货优先级队列（见下） |
| 优先级 | `shipping.jobs`：`x-max-priority=5`，VIP=5，普通=1 |
| 溢出 drop-head | `notify.sms`：`x-max-length=5` |
| 溢出 reject-publish | `inventory.deduct`：`x-max-length=5` |
| 死信 DLX + x-death | 库存队列绑定 `order.dlx`；`x-delivery-limit=3` |
| Publisher Confirm | 凡是会 `basic_publish` 的进程都 `confirm_delivery()` + persistent |
| Manual ACK + prefetch | 所有消费者手动确认；发货 `prefetch=1`，其余 `10` |
| 幂等 | SQLite `processed_ids` + 订单状态机 |
| Heartbeat / Channel | 每进程 1 Connection + 1 Channel，heartbeat=30 |
| TTL 队头阻塞 | 手册和注释说明「为什么关单用延迟插件而不是单条 expiration」；代码不走这条反模式 |

优先级队列必须用 **经典队列**：仲裁队列不支持 `x-max-priority`。这是选型对比的一部分，不是疏忽。

## 4. 业务状态机

订单状态只允许：

`unpaid` → `paid` → `shipped`  
`unpaid` → `cancelled`

规则：

- 超时 worker 只有看到 `unpaid` 才关单并发 `order.cancelled`
- `pay.py` 看到 `cancelled` 则拒绝；已是 `paid` 则幂等成功、不再重复发事件
- 扣库存只处理 `paid` 且未扣过的订单
- 不引入库存不足失败；`--poison` 是故意抛错，用来打满投递次数

演示用单个 SKU：`SKU-DEMO`，初始库存 `1000`。

## 5. 拓扑

### 5.1 交换机

| 名称 | 类型 | durable | 关键参数 |
| --- | --- | --- | --- |
| `order.events` | topic | true | `alternate-exchange=unroutable.ae` |
| `order.delay` | x-delayed-message | true | `x-delayed-type=direct` |
| `inventory.commands` | direct | true | — |
| `notifications` | fanout | true | — |
| `unroutable.ae` | fanout | true | — |
| `order.dlx` | topic | true | — |

全部交换机 durable。绑定两端都 durable，避免「半持久化」导致重启丢 binding。

### 5.2 队列

| 队列 | 类型 | 绑定 | 参数 |
| --- | --- | --- | --- |
| `order.timeout` | quorum | 仅绑定 `order.delay`，routing key `order.timeout` | 无长度限制 |
| `inventory.bridge` | quorum | `order.events`：`order.paid`、`order.cancelled` | — |
| `inventory.deduct` | quorum | `inventory.commands` / `deduct` | DLX=`order.dlx`，`x-delivery-limit=3`，`x-max-length=5`，`x-overflow=reject-publish` |
| `inventory.restore` | quorum | `inventory.commands` / `restore` | 同 DLX 与 delivery-limit，不设短长度限制 |
| `shipping.jobs` | classic | `order.events` / `inventory.deducted` | durable，`x-max-priority=5` |
| `notify.sms` | classic | `notifications`（fanout） | durable，`x-max-length=5`，`x-overflow=drop-head`，DLX=`order.dlx`（被挤出的消息可在死信里看到 `maxlen`） |
| `notify.email` | classic | `notifications` | durable，无长度限制 |
| `notify.app` | classic | `notifications` | durable，无长度限制 |
| `order.dead` | quorum | `order.dlx` / `#` | — |
| `audit.unroutable` | classic | `unroutable.ae` | durable |

`inventory.restore` 与 `inventory.deduct` 分开，避免还库存命令和扣库存命令挤在同一条有 `x-max-length=5` 的队列里。

### 5.3 消息格式

Persistent（`delivery_mode=2`），`content_type=application/json`。

属性：

- `message_id`：UUID，用于 `processed_ids`
- `priority`：发往 `shipping.jobs` 的消息必须带；VIP=5，普通=1。快乐路径里由 `inventory_worker` 发 `inventory.deducted` 时写入；路径 3 由 `seed_shipping_priority.py` 写入。
- `headers.x-delay`：仅延迟消息，毫秒，默认 `15000`

JSON body 字段固定：

```json
{
  "order_id": "ord_...",
  "sku": "SKU-DEMO",
  "qty": 1,
  "vip": false,
  "event": "order.created",
  "ts": "2026-08-15T14:00:00+08:00"
}
```

`event` 与 Topic routing key 一致（命令消息的 `event` 为 `inventory.deduct` / `inventory.restore`）。

## 6. 进程与文件

全部放在 `rabbitmq/order-demo/`。

```
rabbitmq/order-demo/
  docker-compose.yml
  Dockerfile.rabbitmq          # 4-management + delayed plugin
  README.md                    # 演练手册
  connection.py
  topology.py
  db.py
  place_order.py
  pay.py
  debug_publish.py
  seed_shipping_priority.py
  flood_sms.py
  flood_inventory.py
  workers/
    timeout_worker.py
    inventory_bridge.py
    inventory_worker.py
    restore_worker.py
    shipping_worker.py
    notify_sms.py
    notify_email.py
    notify_app.py
    dead_letter_worker.py
    unroutable_worker.py
```

职责：

| 文件 | 做什么 | 依赖 |
| --- | --- | --- |
| `connection.py` | 创建 BlockingConnection（heartbeat=30）+ 单 Channel；只要这个进程会 publish，就 `confirm_delivery()` | Broker |
| `topology.py` | 幂等声明全部 exchange/queue/binding；进程启动先跑 | Channel |
| `db.py` | SQLite：订单、库存、processed_ids；状态迁移函数 | 本地文件 `order-demo.sqlite` |
| `place_order.py` | 插入 `unpaid` → Confirm 发 `order.created` → Confirm 发延迟消息；`--vip`；`--bad-key` 额外再发一条 `order.unknown`（订单本身仍正常创建） | topology, db |
| `pay.py` | 状态机支付 → Confirm 发 `order.paid` | topology, db |
| `inventory_bridge.py` | `order.paid` → Direct `deduct`；`order.cancelled` → Direct `restore` | 手动 ACK |
| `inventory_worker.py` | 扣库存，成功则 Confirm 发 `inventory.deducted`（`priority` 按 vip 设 5 或 1）；`--poison` 每次都失败 | db 幂等 |
| `restore_worker.py` | 还库存（关单补偿） | db 幂等 |
| `timeout_worker.py` | 仍 `unpaid` 则改为 `cancelled` 并发 `order.cancelled` | db |
| `shipping_worker.py` | `prefetch=1`（优先级否则失效）；`--slow` 时每条 sleep 2s；完成后发 `order.shipped` 并往 fanout 发通知 | — |
| `notify_*.py` | 打印渠道名和订单号后 ACK | — |
| `dead_letter_worker.py` | 打印 `x-death` 后 ACK | — |
| `unroutable_worker.py` | 打印无法路由的消息后 ACK | — |
| `flood_sms.py` | 经 Default Exchange 只往 `notify.sms` 打入 >5 条（不影响 email/app） | — |
| `flood_inventory.py` | 往 `inventory.commands` / `deduct` 打入 >5 条 | — |
| `seed_shipping_priority.py` | 经 Default Exchange 往 `shipping.jobs` 塞 3 条 priority=1 + 1 条 priority=5 | — |
| `debug_publish.py` | Default Exchange 对照：发一条到任意已存在队列名 | — |

通知三个 worker 保持独立进程（体现 Fanout 多消费者各有队列），不要合并成一个文件靠参数切换。

启动约定：每个 worker `main` 里先 `declare_topology()` 再 `basic_consume`。生产者同样先声明再发，避免顺序依赖。

## 7. 数据流

### 7.1 快乐路径

1. `place_order.py` 写 `unpaid`，发 `order.created`（可无消费者），发 delay=15s 的超时检查。
2. `pay.py` 把订单改为 `paid`，发 `order.paid`。
3. `inventory_bridge` 发 Direct `deduct`。
4. `inventory_worker` 扣库存（按 `order_id` 幂等），发 `inventory.deducted`。
5. `shipping_worker` 发货，发 `order.shipped`，再发 fanout 通知。
6. 三个 notify worker 各打一行日志。
7. 之后超时消息到达：timeout worker 见已 `paid`，只 ACK，不关单。

### 7.2 超时关单

不支付。15 秒后 timeout worker 将 `unpaid` → `cancelled`，发 `order.cancelled`。bridge 发 `restore`（库存未扣则 restore worker 幂等空操作）。

### 7.3 故意失败与溢出

- `--poison`：inventory_worker 对消息抛错 → `nack(requeue=true)` → 投递满 3 次进 `order.dead`，reason=`delivery_limit`。
- `--bad-key`：额外往 `order.events` 发 `order.unknown`，进 `audit.unroutable`。
- `flood_sms.py`：先停 `notify_sms` worker，再往 `notify.sms` 打入超过 5 条；队头被挤出，死信 reason=`maxlen`。
- `flood_inventory.py`：先停 `inventory_worker`，再往 `deduct` 打入超过 5 条 Ready 消息；第 6 条起生产者 Confirm 收到 nack。

## 8. 可靠性与错误处理

三条泄漏对应实现：

1. **发出去**：所有 `basic_publish` 在已 `confirm_delivery()` 的 Channel 上进行，未收到 ack 则进程以非 0 退出。注释写明：pika BlockingConnection 这是 publish-and-wait；生产应改异步 Streaming Confirms。
2. **Broker 内**：核心 quorum + 全部 durable + persistent。单节点 quorum 在注释和 README 写明：生产至少 3 节点。
3. **消费**：`auto_ack=False`；**先提交 SQLite 再 ACK**。处理失败：库存毒消息 `nack(requeue=true)`，靠 `x-delivery-limit` 进死信，禁止在经典队列上无限 `requeue=true`。

Channel 规则：不跨线程共享；不在每条消息上开关 Channel；`topology.py` 参数必须与已有实体一致，否则 Channel 会被 Broker 关掉。

幂等：

- `processed_ids(message_id TEXT PRIMARY KEY)` 插入冲突视为重复，直接 ACK
- 订单行更新带 `WHERE status=?` 条件，防止超时与支付竞态

SQLite 文件路径：`rabbitmq/order-demo/order-demo.sqlite`（gitignore）。

## 9. 环境

`docker-compose.yml` 只起 Broker，不用社区第三方镜像：

- `Dockerfile.rabbitmq`：`FROM rabbitmq:4-management`
- 在镜像构建时下载 **与该 4.x 小版本匹配、且 pinned 到具体 release tag** 的 `rabbitmq_delayed_message_exchange` `.ez` 插件，放入插件目录，并 `rabbitmq-plugins enable --offline rabbitmq_delayed_message_exchange`
- 端口：`5672`（AMQP）、`15672`（管理台，guest/guest 仅本机）
- 应用连接 `localhost:5672`，与现有教程一致
- 不把 Python worker 打进 Compose；学习时要自己开多个终端看日志
- README 用 `rabbitmq-plugins list` 验证 delayed 插件为 `[E*]`

`.gitignore` 增加 `rabbitmq/order-demo/order-demo.sqlite`。

## 10. 演练手册（验收）

README 必须按顺序给出：compose 启动、声明拓扑（任意脚本都会声明）、要开哪些 worker 终端、每条路径的命令和**预期日志关键字**。

| # | 路径 | 预期 |
| --- | --- | --- |
| 1 | 下单 → 支付 → 扣库存 → 发货 → 三端通知 | 三端各一条日志；订单状态 `shipped` |
| 2 | 下单后不支付 | 约 15 秒后 `cancelled`；timeout worker 打关单日志 |
| 3 | `seed_shipping_priority.py` 先塞 3 普通再塞 1 VIP | `shipping_worker --slow`（每条 sleep 2s）；VIP 先于剩余普通单完成 |
| 4 | `inventory_worker --poison` | 同一 `order_id` 重试后进死信；`x-death` reason=`delivery_limit` |
| 5 | `place_order --bad-key` | `unroutable_worker` 打出原 routing key |
| 6 | `flood_sms` | sms 只留最新 5 条；死信出现 `maxlen` |
| 7 | `flood_inventory` | 生产者打印 Confirm nack / 发布被拒 |

路径 3 的做法固定为：先停 `shipping_worker`，运行 `seed_shipping_priority.py`（Default Exchange → `shipping.jobs`，3×priority=1 后 1×priority=5），再启动 `shipping_worker --slow`。不要用完整下单链路做这条，避免库存/支付状态干扰观察。

路径 6、7 必须先停掉对应消费者，否则消息会被消费掉，队列长度限制看不到。

## 11. 代码风格

- 继续用仓库现有 **Python 3.9 + pika**，不新增 Web 框架
- 中文注释只写「为什么」（对照笔记中的坑），不写复述代码的废话
- 每个队列声明旁用注释标出：类型、DLX、overflow、priority、prefetch 的原因
- 不修改 `rabbitmq/hello-world` 等现有教程目录

## 12. 实现顺序（给后续 plan 用）

1. Docker + 能声明拓扑并在管理台看到实体
2. SQLite + 下单/支付 + Confirm
3. 延迟关单
4. bridge + 库存 + 死信
5. 发货优先级 + fanout 通知
6. AE、两种 overflow、default exchange 对照
7. README 七条演练全部手跑通过
