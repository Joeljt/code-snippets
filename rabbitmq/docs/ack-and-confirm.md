## Consumer Acknowledgements and Publisher Confirms

如果把之前学的 Exchange/Queue 比作“邮局的路线图”**，那这一页讲的就是**“寄挂号信时的回执单”**——它是保证消息在传输过程中**绝对不丢失、不漏处理**的**基石机制。

虽然咱们之前提过 Ack 和 Confirms，但这一页的细节确实值得花 3 分钟精读一下，它能帮你彻底写出**生产级零丢包**的代码！

---

### 🛑 核心要点 1：消费端确认（Consumer Delivery Acknowledgements）

当 RabbitMQ 把消息推给消费者后，它怎么知道这条消息可以安全删除了？

* **自动确认模式（Automatic / `autoAck = true`）**：
* **机制**：消息一通过 TCP 发出去，Broker 建立发送记录后就**立刻把消息从队列删掉**（也叫“发完即忘 Fire-and-Forget”）。
* **致命风险**：如果消费者还没来得及处理，业务代码抛了异常、或者机器突然断电宕机，**消息就彻底永久丢失了**！极不安全。


* **手动确认模式（Manual / `autoAck = false`）** 🌟 **生产必用**：
* **机制**：消费者收到消息并处理完业务逻辑后，主动向 Broker 发送一个确认信号：
* `basic.ack`（正向确认）：告诉 Broker“我处理成功了，可以删除了”。
* `basic.nack` / `basic.reject`（负向确认）：告诉 Broker“我处理失败了”。可以通过设置 `requeue=true` 让消息重新入队给别的机器处理，或者设置 `requeue=false` 让它投递到死信队列（DLX）。


> ⚠️ **关键坑点：Delivery Tag（投递标签）**
> 每条推送的消息都会带一个递增的数字标签叫 `deliveryTag`。**必须在接收消息的同一个 Channel 里回复 ACK**！如果跨 Channel 回复，Broker 会抛出 `PRECONDITION_FAILED - unknown delivery tag` 错误并关闭 Channel。

---

### 🛑 核心要点 2：消费限流与 QoS Prefetch（预取值）

* **痛点**：如果不做限制，开启手动确认时，Broker 会瞬间把队列里的几万条消息全部压给消费者，直接把消费者的**内存挤爆（OOM）**。
* **解决方案（Channel Prefetch）**：
* 使用 `basic.qos(prefetchCount)` 来设定**滑动窗口大小**（比如设为 `100`）。
* **含义**：告诉 Broker，“在这个 Channel 上，未收到 ACK 的消息最多只能有 100 条。如果不满 100 条你继续推，一旦达到了 100 条，就**暂停给我发新消息**，直到我 ACK 掉一部分为止”。
* 💡 **最佳实践**：推荐把 Prefetch 设在 **100 ~ 300** 之间，既能保证极高的吞吐量，又不会挤爆内存。



---

### 🛑 核心要点 3：生产端确认（Publisher Confirms）

前面讲的是“消费端不丢消息”，那“生产者发消息给 Broker”时如果网络波动丢包了怎么办？

* **Publisher Confirms 机制**：
* 生产者将 Channel 设置为 `confirmSelect()` 开启确认模式。
* 消息发送后，Broker 在收到消息并正确写入磁盘/队列后，会异步给生产者回传一个 `ack` 信号；如果 Broker 内部出错了，会回复 `nack`。
* **关键认知**：Publisher Confirms 和 Consumer Ack **完全无关、独立运行**。生产者发消息的 Confirm 只要拿到，就说明消息已经安全躺在 Broker 的队列里了！



---

### 💡 一句话通关总结

> 1. **发消息**：开启 **Publisher Confirm**，确保消息安全进队列。
> 2. **收消息**：开启 **Manual Ack（手动确认）**，业务处理成功再发 `basic.ack`。
> 3. **防压垮**：配置 **QoS Prefetch = 100**，防止消息涌入挤爆消费端内存。
> 