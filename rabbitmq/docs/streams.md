## Streams（流模式）

整个 **[Streams（流模式）](https://www.rabbitmq.com/docs/streams)** 章节全景式地覆盖了 RabbitMQ 针对“海量数据积压”和“高吞吐追溯”场景推出的黑科技。

为了方便你建立完整的知识骨架，我把整个 Streams 模块的核心内容梳理为以下 **5 个维度**：

---

### 1. 核心定位与本质（对标 Kafka）

* **Append-Only Log（追加日志）**：Stream 的本质是保存在磁盘上的追加日志，与传统队列消费即删除（Destructive）不同，Stream 消费后**数据依然留在磁盘**（Non-destructive）。
* **核心优势**：
* **消息回放（Replay）**：可以随时指定 Offset（偏移量）或时间戳，重新读取历史数据。
* **海量广播（Fan-out）**：多个 Consumer 共享同一份 Stream 数据各自读取，无需创建多个队列。
* **海量积压低消耗**：即便积压 GB/TB 级消息，内存占用依然低且平稳。



---

### 2. 核心架构与扩展模式

* **[Single Active Consumer](https://www.rabbitmq.com/docs/streams#single-active-consumer)**：多实例连接同一个 Stream，由 RabbitMQ 选出 1 个作为主节点独占消费，实现极高吞吐下的严格顺序性；主节点挂掉后自动 Failover 选出新主节点。
* **[Super Streams（分区流）](https://www.rabbitmq.com/docs/streams#super-streams)**：当单个 Stream 达到性能上限时，通过 Routing Key Hash 将一个逻辑 Stream 拆分为多个 Partition 子 Stream，实现**横向扩展（Scale-out）**。

---

### 3. [Stream Filtering（流过滤）](https://www.rabbitmq.com/docs/stream-filtering)

解决“Stream 里有海量数据，但 Consumer 只需要其中一小部分”的性能问题，采用 **3 阶段过滤**：

1. **[Bloom Filter](https://www.rabbitmq.com/docs/stream-filtering#stage-1-chunk-level-filtering-in-the-broker)**（磁盘级）：根据 Header 中的 Bloom Filter，直接跳过不含目标消息的 Chunk，**无需读取磁盘**。
2. **[AMQP / SQL Filter](https://www.rabbitmq.com/docs/stream-filtering#stage-2-message-level-filtering-in-the-broker)**（服务端内存级）：对读入内存的消息进行精细筛选，只把匹配的消息发往网络，**极大省带宽**。
3. **Client-Side Filter**（客户端级）：业务代码做最终的精细过滤。

---

### 4. 访问协议与客户端接入

Stream 支持两种通信通道：

* **传统 AMQP 0-9-1 协议（5672 端口）**：
* 只需声明时传参 `x-queue-type: stream`，直接使用常规 AMQP 客户端。
* 消费时通过 `x-stream-offset`（`first`/`last`/`next`/特定 Offset）指定读取位置。
* ⚠️ 消费必须配置 `basic.qos` 预取限制。


* **[Stream Plugin 专用协议](https://www.rabbitmq.com/docs/stream)（5552 端口）**：
* 需在服务端开启 `rabbitmq_stream` 插件。
* 使用官方专用的二进制 [Stream SDK](https://github.com/rabbitmq)（Java, Go, .NET, Rust 等），能解锁极致的百万级 TPS 吞吐量、信用流控（Credit Flow）以及原生 Consumer Group（消费者组）。



---

### 5. 生产与运维调优 ([Stream Connections](https://www.rabbitmq.com/docs/stream-connections))

* **Data Locality（零拷贝优化）**：生产者建议直接连接包含 Leader 的 Broker 节点；消费者可以连接 Leader 或 Replica 节点（利用 `sendfile` 零拷贝分摊读压力）。
* **容器化（Docker/K8s）坑点**：外部客户端需要借助 `advertised_host` 和 `advertised_port` 获取真实的节点访问地址，避免被容器内网 IP 阻断。

---

### 💡 一句话总结选型建议

> **需要任务拆分、重试死信、消费完即清理的业务** ➡️ **[Quorum Queues](https://www.rabbitmq.com/docs/queues)**
> **需要海量数据追溯、历史重放、海量广播、极致高吞吐的业务** ➡️ **[Streams](https://www.rabbitmq.com/docs/streams)**