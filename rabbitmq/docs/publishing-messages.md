## Publishers

🛑 需要花 1 分钟停留并理解的（进阶核心）：

**Strategies for Using Publisher Confirms（发布确认策略）**：

**处理方式**：直接看它提到的三种策略。记住结论：Streaming Confirms（异步回调）是生产推荐的最优解；Publish-and-Wait 是反模式，极度拉低性能。

**为什么重要**：这关系到你的代码怎么写才能保证发送消息不丢。

**Effects of Resource Alarms（资源警报的影响）**：

**处理方式**：只读第一段。

**为什么重要**：建立一个概念——当 RabbitMQ 内存或磁盘满了，它会直接卡死/拒绝所有写消息的连接。以后生产环境遇到发送超时，第一时间想到了解是不是 Broker 满了。

## Exchanges

🛑 唯一需要你停下来记一笔的重点：

**Binding Durability（绑定关系的持久化机制）**

**核心考点**：绑定关系（Binding）的持久化是继承自它两端的组件的。

**生产大坑**：如果你的 Exchange 是持久化的，但绑定的队列是临时的（Transient Classic Queue），当 RabbitMQ 节点重启时，这个临时队列连同它们之间的绑定关系会被直接删掉。哪怕后来节点恢复了，绑定关系也消失了，消息就再也路由不过去了。

**避坑指南**：官方在文中严重警告，在生产中无脑将 Exchange、Queue（使用 Quorum Queue）和 Binding 全都设为 Durable（持久化），不要玩弄“半持久化”的擦边球。未来 RabbitMQ 4.x 版本也会彻底移除对非持久化实体的支持。

💡 只需要留个印象的闪光点（知道有这回事就行）：

**Default Exchange（默认交换机）**：你平时用代码直接往一个“空字符串 ""”的 Exchange 发消息，并指定 Routing Key 为队列名，消息就能直接进队列。这就是默认交换机在起作用，它其实是一个暗中把所有队列用队列名绑在一起的 Direct Exchange。

**Exchange-to-Exchange Bindings（交换机绑定交换机，简称 E2E）**：RabbitMQ 允许你把一个 Exchange 绑定到另一个 Exchange 上，而不是只能绑定队列。这在复杂的架构拓扑、或者做平滑迁移时很有用。

**Alternate Exchanges（备份交换机）**：一句话大白话：消息发出去后，如果没有任何队列能匹配它（无路可走），默认会被丢弃。但如果你配置了“备份交换机”，RabbitMQ 就会把这些流浪的消息转发到这个备份交换机里兜底，通常用来收集错误路由的消息或做审计。

✈️ 可以直接1秒滑过去不看的内容：

**Exchange Types 里的具体介绍**：Fanout、Direct、Topic 的匹配规则（如 * 和 #），你在 Get Started 教程里已经滚瓜烂熟了，直接跳过。

**各种小众 Exchange**：如 JMS Topic、Local Random、Modulus Hash 等，这些是特定插件或边缘场景用的，公司 99% 用不到。

