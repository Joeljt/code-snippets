# 1) 基础镜像：选 slim，兼容性好且比完整 python 镜像小
FROM python:3.12-slim

# 2) 容器内工作目录（后续 COPY/CMD 相对这里）
WORKDIR /app

# 3) 先只拷贝依赖清单时，适合「有 requirements 的项目」做缓存；
#    本 demo 无第三方依赖，直接拷贝代码即可
COPY app.py .

# 4) 声明「容器内」监听端口（文档性质；真正映射靠 docker run -p）
EXPOSE 9000

# 5) 容器启动时执行的主进程（exec 形式，信号可正确传给 Python）
CMD ["python", "app.py"]
