# hello-compose

阶段 5 结业练习：`web` 通过服务名连接 `redis`，用访问计数证明「同网络 + 命名卷」。

概念说明见 [`docs/05-docker-compose.md`](../../docs/05-docker-compose.md)。

```bash
cd docker/demos/hello-compose

docker compose up -d --build
curl http://127.0.0.1:8000/
# 多次 curl，hits 应递增：... hits=1 ... hits=2 ...

docker compose down
docker compose up -d
curl http://127.0.0.1:8000/
# hits 应接上次（卷还在）；若要清空：docker compose down -v

# 排障练习（可选）：把 REDIS_HOST 改成 localhost 再 up --build，应 503；改回 redis 恢复

docker compose exec redis redis-cli GET hello:hits
docker compose logs -f web
```
