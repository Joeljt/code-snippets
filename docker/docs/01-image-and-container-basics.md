# 01. 镜像与容器基石：生命周期、Tag 策略与运行机制

本节总结 Docker 最核心的心智模型：区分镜像与容器、解构 `docker run` 与 `docker start` 的底层边界、理解镜像标签（Tag）的版本控制机制，以及剖析 Alpine 轻量基础镜像的原理与选型注意项。

---

## 一、 核心心智模型：镜像 (Image) vs 容器 (Container)

| 维度 | 镜像 (Image) | 容器 (Container) |
| :--- | :--- | :--- |
| **面向对象类比** | **类 (Class)** / 模板 | **对象实例 (Instance)** / 进程空间 |
| **可变性** | **严格只读 (Read-Only)**，由多层联合文件系统叠加而成 | **可读写 (Read-Write)**，在只读镜像层顶部添加一层临时可写层 |
| **运行时状态** | 静态文件，存储于本地镜像库或远端 Registry | 动态运行中的一组隔离进程，受 Linux Namespace 与 Cgroups 控制 |
| **隔离边界** | N/A | 隔离了进程树 (PID)、网络栈 (NET)、挂载点 (MNT) 等，但**共享宿主机 Linux 内核** |

> **关键认知**：  
> 容器并不是传统意义上的“虚拟机”，它并不虚拟出独立的硬件或 Guest OS 内核，而是利用内核的 Namespace 和 Cgroups 特性被隔离出来的受限进程组。

---

## 二、 关键命令解剖：`docker run` vs `docker start`

### 1. 经典误区：为什么 `docker run <容器名>` 会报错？

执行如下命令：
```bash
docker run learn-redis
# 报错：Unable to find image 'learn-redis:latest' locally
```

**根本原因**：
- `docker run` 的目标操作对象是 **【镜像 (Image)】**，语法为 `docker run [OPTIONS] IMAGE [COMMAND]`。
- Docker 会将传入的 `learn-redis` 当成镜像名；未指定 tag 时自动补齐为 `learn-redis:latest`，在本地和公共 Registry 中找不到该镜像时报错。

### 2. 行为边界对比

```text
               +-------------------+
               |    Image (类)     |
               +-------------------+
                         |
                         | docker run (新建实例)
                         v
               +-------------------+
        +----->| Container (Running)|<----+
        |      +-------------------+     |
docker  |                |               | docker
start   |                | docker stop   | restart
(唤醒)  |                v               |
        |      +-------------------+     |
        +------| Container (Exited)|-----+
               +-------------------+
                         |
                         | docker rm (销毁实例)
                         v
                    [彻底删除]
```

- **`docker run`**：从镜像**新建**并启动一个全新的容器实例。如果容器名已存在，会报冲突错误（Conflict）。
- **`docker start`**：**唤醒/开机**一个已经存在的、处于退出状态（Exited）的旧容器，内部状态与数据得以保持。

### 3. `docker run` 典型参数解析

以命令 `docker run -d --name learn-redis -p 6379:6379 redis:7-alpine` 为例：

```bash
docker run \
  -d \                    # Detached: 后台守护进程模式运行，避免日志阻塞终端
  --name learn-redis \    # 为生成的容器实例分配自定义唯一名称（代替随机生成的哈希名）
  -p 6379:6379 \          # 端口映射：<宿主机外部端口>:<容器内部端口>
  redis:7-alpine          # 使用的目标镜像及标签名（<repository>:<tag>）
```

### 4. 容器生命周期管理常用命令速查

| 操作意图 | 命令 | 说明 |
| :--- | :--- | :--- |
| **创建并启动新实例** | `docker run -d --name <name> -p <host:cont> <image>` | 首次初始化容器时使用 |
| **查看运行中的容器** | `docker ps` | 默认仅展示处于 Up 状态的容器 |
| **查看所有状态的容器** | `docker ps -a` | 展示包括已停止 (Exited) 在内的所有容器 |
| **启动已存在的停止容器** | `docker start <name/id>` | 类似开机唤醒 |
| **优雅停止运行中容器** | `docker stop <name/id>` | 发送 SIGTERM 信号，等待超时后发 SIGKILL |
| **强制删除容器** | `docker rm -f <name/id>` | 先强制杀死进程再释放容器可写层 |
| **进入容器交互执行命令** | `docker exec -it <name/id> <cmd>` | 典型：`docker exec -it learn-redis redis-cli` |
| **查看容器输出日志** | `docker logs -f <name/id>` | `-f` 参数跟随实时输出 |
| **配置开机/崩溃自启** | `docker update --restart unless-stopped <name>` | 宿主机/Docker 守护进程重启后自动唤醒 |

---

## 三、 镜像命名规范与 Tag 版本控制策略

### 1. 命名完整结构

镜像名称遵循 `<repository>:<tag>` 规范：
- `repository`：服务/应用标识（如 `redis`, `rabbitmq`, `nginx`）。
- `tag`：版本或发行版变体（如 `7-alpine`, `3-management`, `7.2.5`）。

### 2. 省略 Tag 的风险：`:latest` 陷阱
- 若不声明 Tag（例如直接写 `redis`），Docker 默认隐式追加 `:latest`。
- **核心缺陷**：`:latest` 并不具备确定性（Non-deterministic），两次执行拉取到的可能跨越了不兼容的主版本号，破坏构建的**幂等性**。**生产环境严禁使用 `:latest`**。

### 3. 语义化版本（SemVer）锁定粒度与选型

依据需求平衡「环境稳定性」与「自动安全修复」：

```text
 粒度分类          示例                     适用场景 / 行为特征
────────────────────────────────────────────────────────────────────────
 精确锁死        redis:7.2.5           生产发布首选，完全幂等，杜绝意外变更
 锁定次版本      redis:7.2             允许自动打入 Patch 修复，保持 API 兼容
 锁定主版本      redis:7               仅限大版本内演进，方便本地长期学习/调试
 追踪最新        redis:latest          仅用于快速验证最新特性，高风险
```

---

## 四、 基础镜像变体深度剖析：为什么常见 `alpine`？

在官方镜像列表里，经常见到 `latest`、`alpine`、`slim` 等后缀。

### 1. 常见标签变体对比

| 变体后缀 | 底层系统 | 平均体积 | C 标准库 | 优缺点与适用场景 |
| :--- | :--- | :--- | :--- | :--- |
| **标准版** (如 `redis:7`) | Debian / Ubuntu | ~150MB | **glibc** | 体积大、包含常用工具、兼容性最优，排障方便 |
| **`-slim`** (如 `python:3.11-slim`) | Debian 精简裁剪 | ~100MB | **glibc** | 移除了文档和不常用包，保持 glibc 良好兼容性 |
| **`-alpine`** (如 `redis:7-alpine`) | Alpine Linux | **~35MB** | **musl libc** | 体积极小，启动飞快，资源占用极低；生产/本地首选 |

### 2. Alpine 极致轻量的核心原因
1. 基础操作系统本身仅 ~5MB。
2. 剔除了传统 Linux 的富工具链，仅保留 BusyBox 工具集（提供精简版常用命令）。
3. 采用轻量级 **musl libc** 代替庞大的 GNU C Library (**glibc**)。

### 3. 选型避坑与边界提示
- **中间件服务（Redis, Nginx, RabbitMQ）**：官方已完成编译与测试，使用 `alpine` 极度稳定且省资源。
- **自定义业务应用构建（Go / Rust / Python / Node.js）**：
  - **静态编译语言（Go / Rust）**：天然契合 Alpine，甚至可压入 `scratch` 空镜像。
  - **动态语言中含 C 扩展库（如 Python numpy/pandas，Node 原生依赖）**：
    由于预编译 wheel 通常针对 `glibc`，在 Alpine（`musl libc`）环境下可能因找不到符号导致运行崩溃，或被迫现场从源码编译导致构建奇慢。  
    👉 **对策**：此类应用优先选用 `-slim` 变体，兼顾体积与 glibc 二进制兼容性。

---

## 五、 中间件版本选型实践：以 Redis 7 vs 8 为例

### 1. 版本现状
- Redis 官方已推出 **Redis 8**，合并了以往 Redis Stack 的 JSON、向量检索（Vector Search）、时序（TimeSeries）等能力。
- 但当前绝大部分企业与教程的主流基线仍停留在 **Redis 6.x / 7.x**。

### 2. 为何当前优先选用 Redis 7？
1. **开源协议变更大地震（2024 年）**：
   - Redis 7.2 之后，背后的商业实体将宽松的开源协议转为双重商业可用协议（RSALv2 / SSPLv1），限制云厂商打包转售。
   - Linux 基金会联合各大厂商以最后的开源版本（Redis 7.2.4）为基准 Fork 出了 **Valkey**。因此业界对升至 8 较为谨慎，许多直接留在 7.2 或转向 Valkey。
2. **核心特性高度稳固**：
   - 学习与常规业务涉及的数据结构（String, Hash, List, Set, ZSet）、TTL 机制、持久化（RDB/AOF）、分布式锁、事务等在 7.x 中成熟稳健。
3. **Docker 带来的试错自由**：
   - Docker 隔离了环境依赖。若日后有 AI 向量检索或 JSON 查询需求，随时可通过更改 Tag 验证 Redis 8，无任何本地环境污染。
