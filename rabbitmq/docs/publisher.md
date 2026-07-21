## Publishers

🛑 需要花 1 分钟停留并理解的（进阶核心）：

**Strategies for Using Publisher Confirms（发布确认策略）**：

**处理方式**：直接看它提到的三种策略。记住结论：Streaming Confirms（异步回调）是生产推荐的最优解；Publish-and-Wait 是反模式，极度拉低性能。

**为什么重要**：这关系到你的代码怎么写才能保证发送消息不丢。

**Effects of Resource Alarms（资源警报的影响）**：

**处理方式**：只读第一段。

**为什么重要**：建立一个概念——当 RabbitMQ 内存或磁盘满了，它会直接卡死/拒绝所有写消息的连接。以后生产环境遇到发送超时，第一时间想到了解是不是 Broker 满了。



