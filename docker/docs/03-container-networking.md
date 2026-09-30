# 03. 容器网络：端口映射、自定义网络与互通路径

本节建立 Docker 网络的够用心智模型：**每个容器有自己的网络命名空间（自己的 localhost）**；  
`-p` 解决「宿主机如何进容器」；**自定义网络**解决「容器之间如何按名字互访」。  
更底层的交换机 / 路由 / OSI 可另学计算机网络；此处只覆盖编排容器时天天用到的部分。

---

## 一、 三张必须分开的图

```text
① 端口映射（给人 / 本机进程用）

   宿主机 :6380  ──-p 6380:6379──►  容器内 Redis :6379


② 绕道宿主机（容器 → host.docker.internal → 再进另一容器）

   临时容器 ──► host.docker.internal:6380 ──► 宿主机转发 ──► lredis:6379


③ 同网络直达（正道，Compose 常用）

   客户端容器 ── learn-net ──► lredis:6379
   （用容器名解析 IP，连的是容器内监听端口，与 -p 无关）
```

| 概念 | 一句话 |
| :--- | :--- |
| **端口映射 `-p`** | 把「容器内端口」发布到「宿主机端口」 |
| **容器网络命名空间** | 每个容器有自己的网卡与 `localhost`，互不通用 |
| **自定义网络 `--network`** | 把相关容器放进同一虚拟局域网，可用容器名互访 |

---

## 二、 为什么容器里的 `localhost` 不是宿主机？

`localhost` / `127.0.0.1` 永远指向**当前网络命名空间自己**。

- 在宿主机上：`127.0.0.1:6379` → 宿主机上监听 6379 的进程（常常是 `-p` 转发出来的口）
- 在容器 A 里：`127.0.0.1:6379` → **只有 A 自己**；连不到同机其它容器里的 Redis

因此：应用容器里写 `redis://localhost:6379`，在 Docker 场景下通常是错的（除非 Redis 就在**同一个**容器里）。

---

## 三、 `-p` 端口映射：只给「从外进宿主机」用

格式永远是：

```text
-p <宿主机端口>:<容器端口>
```

示例：`-p 6380:6379`

| 谁来连 | 应使用的端口 |
| :--- | :--- |
| 浏览器 / 本机客户端 / `host.docker.internal` | **6380**（左边） |
| 同一 Docker 网络内其它容器（`-h lredis`） | **6379**（右边，容器内真实监听端口） |

口诀：

> **同网络互访看容器内监听端口；`-p` 只给宿主机（或绕宿主机）用。**

容器间通信**不需要** `-p`；没有映射时，同网络仍可用容器名 + 内部端口互通，只是宿主机直接访问不了。

---

## 四、 两条互通路径对比

### 路径 A：`host.docker.internal`（旁路，Desktop 常用）

`host.docker.internal` 是 Docker Desktop（Mac/Windows）提供的特殊 DNS，在容器内解析到**宿主机**。

典型实验：

```bash
# 临时容器只跑客户端（覆盖镜像默认的 redis-server）
docker run --rm redis:7-alpine redis-cli -h host.docker.internal -p 6380 PING
```

链路：

```text
临时容器(redis-cli)
  → host.docker.internal
  → 宿主机:6380（-p 发布）
  → lredis 内 redis-server:6379
  → PONG 打印在临时容器终端
```

要点：

- 本机**不必安装** Redis；6379/6380 上听的是 Docker 端口转发。
- `redis-cli` 跑在**临时容器**；`lredis` 里跑的是 **redis-server**，不是「进到对方容器再执行 cli」。
- `redis-cli -p` 默认就是 6379；若映射是 `6380:6379`，绕宿主机时才需要写成 `-p 6380`。

### 路径 B：自定义网络 + 容器名（正道）

```bash
docker network create learn-net

docker run -d --name lredis \
  --network learn-net \
  -v redis-data:/data \
  redis:7-alpine
  # 容器间互通可不加 -p；若本机也要连，再加 -p

docker run --rm --network learn-net \
  redis:7-alpine redis-cli -h lredis PING
```

- DNS：容器名 `lredis` → 该容器 IP（**自定义 bridge 网络自带 DNS**）。
- 端口：仍须对准服务真实监听端口（Redis 默认 **6379**）。
- `lredis:6380 Connection refused`：名字已解析成功，但容器内 6380 无人监听。

---

## 五、 `--network` ≈ 虚拟局域网；bridge ≈ 二层交换机

| 类比 | 含义 |
| :--- | :--- |
| `docker network create learn-net` | 新建一条虚拟局域网 |
| `--network learn-net` | 把容器「插进」这条网 |
| 同网络内容器名解析 | 内网主机名互访 |
| 编排时相关服务同网络 | App / Redis / MQ 放同一业务网段 |

**bridge** 首先是计算机网络 / Linux 内核概念（二层网桥），不是 Docker 独创。  
Docker `bridge` 驱动底下用的是 Linux bridge（默认常看到 `docker0`）：把各容器的虚拟网卡接到同一二层网络。

- 叫 **bridge（桥）**：在多个二层端口/网段之间搭桥，合成同一广播域。
- 口语可说「像交换机」；现代交换机本质上是多端口网桥。Linux 设备就叫 `bridge`，故 Docker 驱动也叫这个名字（不是 exchange）。

### 隔离边界（重要）

```text
learn-net                         other-net
  app ──┐                           mysql ──┐
  redis─┴─ 虚拟交换机（bridge）              └─ 另一台 bridge
              │
              └── 默认互不通讯（不同局域网，不自动路由）
```

- **同一 network**：bridge 像交换机，二层转发，可互通。
- **不同 network**：默认隔离；bridge **不会**在不同局域网之间自动转发。跨网络需显式 `docker network connect`（双网卡）等，那是路由/多附着问题，不是交换机的职责。

---

## 六、 `docker run` 带命令 vs `docker exec`

| 命令 | 前提 | 作用 |
| :--- | :--- | :--- |
| `docker run ... [命令]` | **新建**容器 | 用给定命令**覆盖**镜像默认启动命令，作为容器主进程 |
| `docker exec ... [命令]` | 容器**已在运行** | 向已有容器再塞一条命令 |

```bash
# 新建短命客户端容器：不跑 redis-server，主进程是 redis-cli
docker run --rm --network learn-net \
  redis:7-alpine redis-cli -h lredis PING

# 进入已在跑的 lredis 里操作
docker exec -it lredis redis-cli PING
```

`--rm`：容器退出后自动删除，适合一次性客户端实验。

---

## 七、 默认 bridge vs 自定义 bridge（选型）

| | 默认 `bridge` | 自定义网络（推荐） |
| :--- | :--- | :--- |
| 容器名 DNS | 基本不可靠 / 需旧式 `--link` | **内置 DNS，容器名可解析** |
| 隔离 | 所有默认网络容器挤一起 | 按业务划分网段 |
| 使用方式 | 不写 `--network` 时的默认 | `docker network create` + `--network` |

学习与编排：**自己建 network，相关容器挂上去**。

---

## 八、 常用命令速查

| 意图 | 命令 |
| :--- | :--- |
| 创建网络 | `docker network create learn-net` |
| 列出网络 | `docker network ls` |
| 查看网络详情（含哪些容器） | `docker network inspect learn-net` |
| 运行中容器接入网络 | `docker network connect learn-net <容器>` |
| 断开网络 | `docker network disconnect learn-net <容器>` |
| 删除网络 | `docker network rm learn-net` |

---

## 九、 够用清单（本节范围）

已经足够支撑后续 Compose / 本地多服务 Demo：

1. 容器有独立网络命名空间；`localhost` 不等于宿主机或其它容器。
2. `-p 宿主机:容器`；对内对外两套端口不要混。
3. 容器间优先：**同一自定义网络 + 容器名 + 内部端口**。
4. `host.docker.internal` 是 Desktop 下「访问宿主机」的旁路，常再经 `-p` 进其它容器。
5. bridge 网络 ≈ 虚拟局域网 + 二层交换机；不同 network 默认隔离。

可暂缓（另学计算机网络或以后进阶）：iptables/NFT 细节、overlay/跨主机、macvlan、生产级网络策略等。

---

## 十、 与下一阶段的衔接

手写多次 `docker run --network ... -v ... -p ...` 会很快变烦。  
下一阶段 **Dockerfile** 解决「如何把应用打成镜像」；再下一阶段 **Compose** 用一份 YAML 声明服务、网络、卷，一条命令拉起整套环境。
