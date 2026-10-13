# 04. Dockerfile 与镜像构建：指令手册、分层缓存与构建上下文

前面用别人的镜像（如 `redis:7-alpine`）是「拿成品」；  
写 `Dockerfile` + `docker build` 是「自己按菜谱做镜像」。

```text
Dockerfile + 构建上下文（目录里的文件）
        │ docker build -t name:tag .
        ▼
     本地镜像
        │ docker run / docker push
        ▼
     容器 / 镜像仓库
```

---

## 一、 核心心智：指令 ≈ 往镜像上叠一层（或改配置）

- **`RUN` / `COPY` / `ADD`**：通常产生文件系统层（真有文件变化）。
- **`ENV` / `WORKDIR` / `EXPOSE` / `CMD` 等**：更多是配置与元数据（`docker history` 里可能是 0B）。
- **缓存规则**：某层输入变了 → 该层及**后面的指令**默认都要重做。少变的靠前，常变的靠后。

---

## 二、 常用指令速查（先掌握这些就够用）

| 指令 | 干什么 | 典型例子 |
| :--- | :--- | :--- |
| **`FROM`** | 指定基础镜像，后面所有指令叠在它上面 | `FROM python:3.12-slim` |
| **`WORKDIR`** | 设定容器内工作目录；之后的 `RUN`/`COPY`/`CMD` 相对此路径；目录不存在会创建 | `WORKDIR /app` |
| **`COPY`** | 从**构建上下文**拷文件进镜像 | `COPY app.py .` |
| **`ADD`** | 类似 `COPY`，额外支持 URL、自动解压 tar（副作用多，**优先用 COPY**） | 一般少用 |
| **`RUN`** | 在构建阶段执行命令（装包、编译），结果写入镜像层 | `RUN pip install -r requirements.txt` |
| **`ENV`** | 设置环境变量（构建后的容器里也能读到） | `ENV PORT=8000` |
| **`ARG`** | **仅构建时**可用的变量（默认不留进运行容器，除非再赋给 `ENV`） | `ARG APP_VERSION=1.0` |
| **`EXPOSE`** | 声明容器打算听的端口（文档 + 配合 `-P`）；**不**等于 `-p` | `EXPOSE 8000` |
| **`CMD`** | 默认启动命令或默认参数；仅 CMD 时可被 `run` 整段覆盖 | `CMD ["python", "app.py"]` |
| **`ENTRYPOINT`** | 固定入口程序；`run` 后面的内容默认变成它的参数 | `ENTRYPOINT ["python"]` |
| **`USER`** | 指定之后指令 / 运行时用哪个用户（安全：避免一直 root） | `USER app` |
| **`VOLUME`** | 声明匿名卷挂载点（易踩坑；现代更常用 run/compose 显式挂卷） | `VOLUME /data` |
| **`LABEL`** | 给镜像打元数据标签 | `LABEL maintainer="you"` |

日常写应用镜像，高频就这几个：  
**`FROM` → `WORKDIR` → `COPY` → `RUN` → `ENV` → `EXPOSE` → `CMD`**。

---

## 三、 逐条讲清（结合 hello-dockerfile）

### 1. `FROM` — 地基

```dockerfile
FROM python:3.12-slim
```

- 和直接 `docker run redis:7-alpine` 用的是**同一类东西**：都是镜像。
- 差别在角色：这里当**原材料**，在上面继续叠你的应用。
- 基础镜像可能主要出现在 build cache 里，`docker images` 不一定总能看到独立的 `python:3.12-slim` 行；成品镜像里已经包含其层。

### 2. `WORKDIR` — 「之后默认在哪个目录干活」

```dockerfile
WORKDIR /app
```

效果近似在构建/运行时：

```bash
mkdir -p /app && cd /app
```

- 后面写 `COPY app.py .` 的 `.` 就是 `/app`。
- `CMD ["python", "app.py"]` 也在 `/app` 下找文件。
- 可多次出现，每次切换当前目录。

没有 `WORKDIR` 时，默认往往在 `/`，路径容易写乱，所以应用镜像几乎总会设一个。

### 3. `COPY` — 把宿主机（上下文）文件放进镜像

```dockerfile
COPY app.py .
# 等价于 COPY app.py /app/app.py（若 WORKDIR 已是 /app）
```

- 左边：构建上下文里的路径（受 `.dockerignore` 过滤）。
- 右边：镜像内路径。
- **只能**拷上下文内的文件，不能 `COPY ../../秘密` 逃出上下文。

```dockerfile
COPY requirements.txt .
COPY app.py .
# 或
COPY src/ /app/src/
```

### 4. `RUN` — 构建时执行（结果写入镜像层）

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

- 发生在 **`docker build` 时**，不是容器每次启动时。
- 装好的依赖成为镜像的一部分；容器启动不必再装一遍。

对比：

| | `RUN` | `CMD` |
| :--- | :--- | :--- |
| 何时执行 | **build** | **run**（每次启动） |
| 典型用途 | apt/pip/npm、编译 | 启动服务进程 |

### 5. `CMD` — 容器默认主进程

```dockerfile
CMD ["python", "app.py"]   # exec 形式（推荐）
```

- 镜像的「默认怎么启动」。
- `docker run 镜像 redis-cli ...` 这类写法会**整段覆盖** `CMD`（你用 Redis 镜像跑 `redis-cli` 时已见过）。
- 推荐 JSON 数组（exec）形式：信号能直接传给进程，便于 `docker stop` 优雅退出。  
  shell 形式 `CMD python app.py` 实际经 `/bin/sh -c` 包装，一般不如 exec 干净。

### 6. `ENTRYPOINT` vs `CMD`

一句话：

> **`ENTRYPOINT` = 固定要跑的程序；`CMD` = 默认参数（可被换成别的参数）。**  
> 只有 `CMD` 时：`docker run 镜像 其它命令` 会把启动命令**整段换掉**。

#### 只有 `CMD`（入门最常见）

```dockerfile
CMD ["python", "app.py"]
```

| 启动方式 | 实际执行 |
| :--- | :--- |
| `docker run 镜像` | `python app.py` |
| `docker run 镜像 redis-cli PING` | `redis-cli PING`（**整段覆盖** CMD） |

用 Redis 镜像跑 `redis-cli`、不跑默认 `redis-server`，就是这种机制。

#### `ENTRYPOINT` + `CMD`（拼在一起）

```dockerfile
ENTRYPOINT ["python"]
CMD ["app.py"]
# 实际命令 = ENTRYPOINT + CMD → python app.py
```

| 启动方式 | 实际执行 | 含义 |
| :--- | :--- | :--- |
| `docker run 镜像` | `python app.py` | 用默认参数 |
| `docker run 镜像 other.py` | `python other.py` | **只换参数**，入口仍是 `python` |
| `docker run 镜像 -c 'print(1)'` | `python -c print(1)` | 同上 |

此时 `docker run` 后面写的内容**不会换掉** `ENTRYPOINT`，而是当成传给它的参数。  
要换掉入口本身，必须显式：

```bash
docker run --entrypoint sh 镜像
```

#### 只有 `ENTRYPOINT`、没有 `CMD`

```dockerfile
ENTRYPOINT ["python"]
# 没有 CMD → 默认没有附加参数
```

| 启动方式 | 实际执行 |
| :--- | :--- |
| `docker run 镜像` | 只有 `python` |
| `docker run 镜像 app.py` | `python app.py` |

不是「协议规定必须在 run 时带参数」；而是默认参数为空。光跑入口有没有意义，取决于这个程序本身（例如光 `redis-server` 往往可以，光 `python` 可能不太适合当服务）。

#### 对照小结

| | 只有 `CMD` | `ENTRYPOINT` +（可选）`CMD` |
| :--- | :--- | :--- |
| `docker run 镜像` | 执行 CMD | 执行 ENTRYPOINT + CMD |
| `docker run 镜像 其它...` | **整段换成**其它 | 其它变成 **ENTRYPOINT 的参数** |
| 换掉入口程序 | 直接写在 run 后面即可 | 需要 `--entrypoint` |

入门镜像只用 `CMD` 完全够；看到官方镜像里的 `ENTRYPOINT`，按「固定程序 + 可换参数」理解即可。

### 7. `ENV` / `ARG`

```dockerfile
ARG PORT_DEFAULT=8000          # 仅 build 时
ENV PORT=8000                  # 写入镜像，容器内可读
```

`app.py` 里 `os.environ.get("PORT", "8000")` 读的就是运行时环境变量；  
`docker run -e PORT=9000` 可覆盖 `ENV`。

### 8. `EXPOSE` — 再强调一次

- 声明「容器内打算听的端口」。
- **不**自动做宿主机映射。
- 配合 `docker run -P`：按 `EXPOSE` 把容器口映射到**随机**宿主机口。
- 显式 `-p 宿主机:容器` 时以 `-p` 为准，与有无 `EXPOSE` 无关。
- 进程真正监听的端口仍由程序 / `ENV` 决定，须与映射的**容器侧端口**一致。

---

## 四、 构建上下文与 `.dockerignore`

```bash
docker build -t hello-dockerfile:dev .
#                                ^^^ 上下文根目录
```

- 引擎会打包上下文（被 ignore 的除外）供 `COPY` 使用。
- 上下文越大，上传/构建越慢；无关文件还可能破坏缓存或泄密。

`.dockerignore` 示例：

```text
.git
__pycache__
*.pyc
.env
*.md
```

---

## 五、 分层缓存（编写重点）

```dockerfile
# 少变：依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 常变：代码
COPY app.py .
CMD ["python", "app.py"]
```

| 写法 | 只改 `app.py` 时 |
| :--- | :--- |
| 依赖与代码同一 `COPY`，再 `pip install` | `pip` **会重跑**（COPY 层已失效，后面全失效） |
| 先只 `COPY requirements` + `RUN pip`，再 `COPY` 代码 | `pip` **可复用缓存** |

规则：某层失效 → Dockerfile **写在后面的指令**默认全部重做。

`FROM` 相同基础镜像的多层在磁盘上可共享（积木复用）；  
`build` 的 layer cache 则是「这层要不要重新执行」——两个相关但不同的概念。

---

## 六、 端口三条线（与 run 相关，常和 Dockerfile 一起搞混）

| 线 | 谁决定 |
| :--- | :--- |
| 进程监听口 | 代码 / `ENV`（如 `PORT`） |
| 发布到宿主机 | `-p` 或（有 `EXPOSE` 时的）`-P` |
| `EXPOSE` | 文档；`-P` 时决定映射的**容器侧**端口 |

从宿主机访问成功，需要：  
**curl 的宿主机口 → 映射到的容器口 → 进程监听口** 一致。  
未做 `-p`/`-P` 时，宿主机进不来，但同网络容器仍可能用容器名+内部口互访。

---

## 七、 镜像仓库：build → tag → push

```bash
docker build -t registry.example.com/team/hello:1.0 .
docker login registry.example.com
docker push registry.example.com/team/hello:1.0
```

名字需带仓库地址；本地短名 `hello:dev` 默认并不知道推到你的私服。  
`docker images` 列的是引擎里的镜像，**不是**项目目录下的二进制文件。

---

## 八、 指令学习优先级

| 优先级 | 指令 |
| :--- | :--- |
| 必会 | `FROM` `WORKDIR` `COPY` `RUN` `CMD` `ENV` `EXPOSE` |
| 常用 | `ARG` `USER` `.dockerignore` 习惯 |
| 稍后 | `ENTRYPOINT` 细合成、多阶段 `FROM ... AS build`、`HEALTHCHECK` |
| 慎用/少用 | `ADD`（无必要不用）、镜像内盲目 `VOLUME` |

---

## 九、 与下一阶段的衔接

会写 Dockerfile 之后，用 **Compose** 把「build 应用 + 拉 Redis + 同一 network + 卷」写成一份 YAML，避免重复手打 `docker run`。
