# hello-dockerfile

阶段 4 练习：把本地 Python 小服务打成镜像并运行。

```bash
cd docker/demos/hello-dockerfile

# 构建镜像（注意末尾的 . 表示构建上下文）
docker build -t hello-dockerfile:dev .

# 运行：宿主机 8000 → 容器 8000
docker run --rm -p 8000:8000 --name hello-df hello-dockerfile:dev
```

另开终端：

```bash
curl http://127.0.0.1:8000/
```
