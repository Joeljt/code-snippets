# hello-compose

阶段 5：用 Compose 一键拉起 `web`（自建镜像）+ `redis`。

概念说明见 [`docs/05-docker-compose.md`](../../docs/05-docker-compose.md)。

```bash
cd docker/demos/hello-compose

docker compose up -d --build
docker compose ps
docker compose config --services
curl http://127.0.0.1:8000/

# 进已有 redis 容器验证（优先用 exec，不要用 run 再起一份）
docker compose exec redis redis-cli PING

docker compose down          # 停并删容器，默认保留命名卷
# docker compose down -v     # 连卷一起删（慎用）
```
