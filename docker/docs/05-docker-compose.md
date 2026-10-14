# 05. Docker Compose：多服务编排、项目资源与常用命令

Compose 把「build / run / 网络 / 卷 / 环境变量」收成一份声明式 YAML，  
用一条命令拉起**一整套多容器环境**（本地 Demo、读公司编排文件的基础）。

配套练习：`docker/demos/hello-compose/`。

---

## 一、 该怎么称呼「Compose 启动的那一套」

| 层级 | 叫法 | 例子 |
| :--- | :--- | :--- |
| 整份 Compose 拉起的整体 | **项目（project）** / **应用栈（stack）** / 这套环境 | `hello-compose` |
| YAML 里 `services:` 下每一项 | **服务（service）** | `web`、`redis` |
| 实际进程实例 | **容器（container）** | `hello-compose-web-1` |

- Compose 起的是 **一个多服务项目/栈**，不是「合并成一个镜像的一个服务」。
- 每个 service 通常对应**一类容器、一份镜像、一个主进程**；它们被编排在一起，进程仍然分离。

Portainer（Standalone）上常见对应：

| Portainer | 含义 |
| :--- | :--- |
| **Stack** | 多为一个 Compose 项目 |
| **Containers** | 所有容器（含 compose 与裸 `docker run`） |
| **Images / Volumes / Networks** | 镜像、卷、网络库存 |
| **Services** | 多为 **Swarm 服务**；≠ YAML 里的 `services` 计数 |

镜像数可以大于容器数：旧 tag、基础镜像、已删栈留下的镜像都还在本地库里。

---

## 二、 心智模型：编排 ≠ 打进同一镜像

```text
项目网络（默认 hello-compose_default）
┌────────────────────────────────────────────┐
│  web  ──主机名 redis:6379──►  redis         │
│   │                         （可不映射宿主机） │
│  ports 8000:8000                            │
└────────────────────────────────────────────┘
         ↑
    宿主机 / 浏览器只打入口服务
```

等价于：分别 `run` 多个容器 + 同一网络 + 卷/环境声明 + 统一生命周期（`up` / `down`）。  
**组合的是运行环境，不是把 web 和 redis 打进同一个镜像。**

---

## 三、 YAML 基础（数组 vs 对象）

| 写法 | 类型 | 例子 |
| :--- | :--- | :--- |
| 缩进后的 `-` | **数组** | `ports: ["8000:8000"]` 或 `- "8000:8000"` |
| `键:` 下再嵌套键 | **对象** | `environment: { PORT: "8000" }` |

```yaml
ports:                 # 值是数组
  - "8000:8000"
environment:           # 值是对象（也可写成 - PORT=8000 数组形式）
  PORT: "8000"
```

---

## 四、 与 `docker run` 对照

| `docker run` | Compose |
| :--- | :--- |
| `docker build` + 镜像名 | `build:` / `image:` |
| `-p 8000:8000` | `ports:` |
| `-e PORT=8000` | `environment:` / `env_file:` |
| `-v redis-data:/data` | 服务下 `volumes:` + 顶层 `volumes:` 声明 |
| `docker network create` + `--network` | 默认同项目网络；或顶层 `networks:` + 服务挂载 |
| `--name` / 重启策略等 | `container_name` / `restart` 等 |

---

## 五、 `build` vs `image`

| 字段 | 含义 |
| :--- | :--- |
| **`build`** | 按 Dockerfile **现场构建**再启动 |
| **`image`** | **直接使用**已有镜像（本地或远程仓库） |

```yaml
web:
  build: ../hello-dockerfile          # 开发常用
  # image: hello-dockerfile:dev       # 也可用已 build 好的本地镜像
  # image: registry.example.com/a:1.0 # 或远程镜像（需时可先 docker login）

redis:
  image: redis:7-alpine               # 第三方现成镜像
```

两者都写时：按 `build` 构建，并打成 `image` 指定的名字（便于 push）。

---

## 六、 网络

### 1. 默认行为

不写 `networks:` 时，Compose 仍会创建项目默认网（如 `hello-compose_default`），  
同文件内服务都加入 → 可用**服务名**做 DNS（`redis`、`web`）。

容器间访问用**容器内端口**（Redis `6379`），与有没有 `ports:` 无关。  
`ports:` 只解决**宿主机（或绕宿主机）**如何进来。

### 2. 显式多网（公司常见）

```yaml
services:
  web:
    networks: [frontend, backend]   # 数组：同一容器可进多张网
  redis:
    networks: [backend]

networks:
  frontend:
  backend:
```

用于隔离：例如 redis 不进 frontend，外界更难直达。

### 3. `external: true`（网络）

```yaml
networks:
  corp_shared:
    external: true    # 使用已有网络，本项目不创建
```

- **`external` ≠ 对外暴露给公网/宿主机**。  
- 含义：资源是否由**当前 Compose 创建**（已有 vs 新建）。  
- 跨多个 compose / 运维预建网络时常用。  
- **宿主机访问**靠 `ports:`（以及 bind mount），与 `external` 无关。

---

## 七、 卷

### 1. 命名卷要顶层声明

```yaml
services:
  redis:
    volumes:
      - redis-data:/data    # 怎么挂

volumes:
  redis-data:               # 声明卷（右边为空 = 默认配置，等价 {}）
```

- **命名卷**（短名）：必须在顶层 `volumes:` 登记，否则现代 Compose 常直接报「未定义」。  
- **Bind**（`./data:/data`）：**不要**写进顶层 `volumes:`。  
- Dockerfile 负责镜像内容；**命名卷生命周期由 run/Compose 管**，所以 Compose 要单独登记项目卷。

### 2. 实际卷名常带项目前缀

| YAML 中的名 | `docker volume ls` 常见结果 |
| :--- | :--- |
| `redis-data`（Compose 默认创建） | `hello-compose_redis-data` |
| 早期 `docker run -v redis-data:/data` | 短名 `redis-data` |

卷存在 **Docker 引擎管理的宿主机存储**（Desktop 上在 Linux VM 里），不是只活在容器可写层。  
`compose down` **默认不删卷**；`down -v` 才会删项目卷。

### 3. `external: true`（卷）

```yaml
volumes:
  redis-data:
    external: true   # 假定宿主机已有该卷；不创建；没有则 up 失败
```

不是「跳过校验、运行时再炸」；缺少 external 卷时一般在 **up 阶段**报错。  
`docker volume rm` 前须先去掉引用该卷的容器（含已停止的）。

---

## 八、 端口与「只暴露入口」

```yaml
web:
  ports:
    - "8000:8000"    # 宿主机:容器
redis:
  # 不写 ports → 仅项目网络内可访问，适合当内部依赖
```

从宿主机访问仍须：**curl 的宿主机口、映射的容器口、进程监听口**一致（见阶段 3 / 4）。

---

## 九、 `command` 与 `restart`

### 1. `command` ≈ 覆盖镜像的 `CMD`

```yaml
redis:
  image: redis:7-alpine
  command: ["redis-server", "--appendonly", "yes"]
```

- 不写 `command`：用镜像默认启动，Redis **照样能跑**。  
- 写上：改启动参数（这里打开 AOF，方便练习卷持久化）。  
- 有 `ENTRYPOINT` 时，Compose 的 `command` 多半是换「传给入口的参数」（同 Dockerfile 里 CMD 与 ENTRYPOINT 的关系）。

### 2. `restart` 可选值

| 值 | 含义 |
| :--- | :--- |
| `no` | 不自动重启（默认） |
| `always` | 总是重启；手动 stop 后，引擎重启仍可能再拉起 |
| `unless-stopped` | 总是重启，但**手动停过**后引擎重启不再拉起 |
| `on-failure` / `on-failure:N` | 仅异常退出（非 0）时重启；可限次数 |

本地练手常用 `unless-stopped` 或省略。

---

## 十、 项目范围命令：`compose ps` / `compose exec`

Compose 子命令相对「裸 docker」多半是**范围缩到当前项目**，并用 **service 名**代替容器 ID。

| | 裸 Docker | Compose |
| :--- | :--- | :--- |
| 列表 | `docker ps`：引擎上**全部**容器；有 NAMES 列 | `docker compose ps`：仅**本项目**；另有 **Service** 列（`web`/`redis`） |
| 进容器执行 | `docker exec -it <容器名或ID> ...` | `docker compose exec <服务名> ...` |

```bash
docker compose exec redis redis-cli PING   # 推荐：按服务名
docker exec -it hello-compose-redis-1 redis-cli PING
```

### `exec` vs `run`

| 命令 | 含义 |
| :--- | :--- |
| `docker compose exec redis redis-cli PING` | 进**已在跑的** redis 容器 |
| `docker compose run --rm redis ...` | **临时再起**一个参照 redis 配置的容器 |

已有 service 时查活优先 **`exec`**。

### 排障：`redis-cli` 必须进 redis 容器

| 容器 | 有没有 `redis-cli` |
| :--- | :--- |
| **redis**（`redis:7-alpine`） | 有 |
| **web**（Python 应用镜像） | **无**（只有 Python 的 redis 库） |

进错 web 再跑 `redis-cli` 会失败；用 `compose exec redis` 可避免抄错 ID。  
容器 recreate 后短 ID 会变，更不要依赖手抄 ID。

查键 / 看落盘文件：

```bash
docker compose exec redis redis-cli GET hello:hits
docker compose exec redis ls -la /data          # AOF/RDB 等（二进制，日常仍以 cli 查数据为主）
```

---

## 十一、 常用命令

```bash
cd docker/demos/hello-compose

docker compose up -d --build   # 后台启动；有 Dockerfile 变更时重建
docker compose ps              # 当前项目容器 + Service 名
docker compose config --services
docker compose logs -f web
docker compose exec redis redis-cli PING
docker compose down            # 停并删容器/默认网；默认保留命名卷
# docker compose down -v       # 连卷一起删（慎用）
```

本 demo 资源量级：

```text
项目/栈:  hello-compose（Compose 称 project；Portainer 常显示为 Stack）
网络:     hello-compose_default（1）
卷:       hello-compose_redis-data（1；YAML 里写 redis-data，默认加项目前缀）
容器:     web + redis（2）
镜像:     hello-compose-web + redis:7-alpine（2）
```

---

## 十二、 结业练习小结（hello-compose）

整体是**编排两个服务**，不是打成一个安装包：

- **web**：对外 `8000`；`environment` 注入 `REDIS_HOST=redis`（服务名 DNS，不是宿主机全局变量）。  
- **redis**：不映射宿主机端口；仅项目网络内给 web 用；数据进**命名卷**。  
- web 处理 HTTP，需要时连 redis（本 demo 用访问计数 `hello:hits`）。  
- `depends_on` 只管大致启动顺序；`command` 开 AOF 为练习持久化。

验证闭环：`curl` 见 `hits` 递增 → `down` 再 `up` 计数仍在（未 `down -v`）→ 可选把 `REDIS_HOST` 改成 `localhost` 看 503，改回 `redis` 恢复。

---

## 十三、 进阶清单（读公司文件够用，可稍后深挖）

| 配置 / 能力 | 作用 |
| :--- | :--- |
| `depends_on` | 启动顺序；**不保证**依赖已「就绪」 |
| `.env` + `${VAR}` | 端口、tag、密钥等外置配置 |
| `healthcheck` | 健康检查；可配合 depends_on 的 `service_healthy` |
| `compose.override.yml` | 本地覆盖（常不提交） |
| `profiles` | 按场景只启动部分服务 |
| `configs` / `secrets` | 配置与密钥（偏生产） |

---

## 十四、 阶段结论（够用版）

已掌握：

1. Compose = 多容器**项目编排**（栈），不是单镜像合并。  
2. `build` / `image`、`ports`、`environment`、命名卷声明、默认网与服务名 DNS。  
3. 显式 `networks` / `volumes` 与 `external: true`（资源是否本项目创建）。  
4. 对外暴露靠 `ports`（及 bind），与 `external` 无关。  
5. `command` / `restart`、`compose ps|exec` 与裸 docker 的范围差异。  
6. web 真正连 redis 的结业闭环，以及 Portainer 上 Stack / Container / Image 的对应关系。

后续学系统设计时，反复「Compose 起栈 → 写业务 → 排障」即可把 Docker 练熟，不必再整本刷运维向教程。
