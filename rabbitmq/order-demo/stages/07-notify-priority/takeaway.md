# Stage 7 Takeaway

> 对应代码：[`topology.py`](topology.py) · [`seed_priority.py`](seed_priority.py) · [`shipping_worker.py`](shipping_worker.py) · [`notify_sms.py`](notify_sms.py)

## 就这点东西

两块独立机制：

1. **经典优先级队列** `shipping.jobs`  
2. **Fanout** `notifications` → `notify.sms`（发货后广播通知）

```
seed_priority ──priority──► shipping.jobs (x-max-priority=5)
                                 │
                          shipping_worker（prefetch=1）
                                 │
                                 ▼
                          notifications (Fanout) ──► notify.sms → notify_sms
```

---

## 优先级

```python
ch.queue_declare(Q_SHIP, durable=True, arguments={"x-max-priority": 5})
ch.basic_publish("", Q_SHIP, body, properties=pika.BasicProperties(priority=5))
```

- `x-max-priority: 5`：本队列按 0～5 档排序；publish 的 `priority` 超过 5 **会压成 5**，不报错  
- 不设 priority → 当 0（最低）  
- **只在 Broker 从 Ready 挑下一条 deliver 时**看优先级  
- 仲裁队列 **不支持** 优先级，所以这里用经典队列  

`prefetch=1` **不是**「打开优先级的开关」。队列自己会按优先级挑；prefetch 太大时多条低优先级先被塞进 consumer（Unacked），后面的 VIP 只能在 Ready 干等，看起来像优先级失效。实践上要观察/依赖优先级，几乎都配 `prefetch_count=1`。

demo：先 `seed`（3×priority=1 + 1×VIP=5，worker 先别开）→ 再 `shipping_worker --slow` → 应先打 VIP。

---

## Fanout

shipping 处理完后 publish 到 `notifications`，忽略 routing key，绑了的队列全收。和优先级无关，只是「发货成功通知一嘴」。

```python
ch.exchange_declare(EX_NOTIFY, ExchangeType.fanout, durable=True)
ch.queue_bind(Q_SMS, EX_NOTIFY)
```

---

## 本阶段命令

```bash
python notify_sms.py
python seed_priority.py          # 先不要开 shipping
python shipping_worker.py --slow
```

## 下一阶段

完整版汇合 → [`../../full/README.md`](../../full/README.md)
