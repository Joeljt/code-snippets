# 02. 存储与持久化：Volume、Bind Mount 与数据生命周期

本节搞清一件事：**容器可以扔，数据不一定跟着扔。**  
核心是区分容器可写层、命名卷、绑定挂载，以及「挂对了卷 ≠ 应用已经把数据刷到磁盘」。

---

## 一、 为什么需要挂载？

容器默认在镜像只读层之上有一层**可写层**。  
`docker rm` 删容器时，这层可写层一起消失——没挂载的话，写在容器里的数据就没了。

挂载要解决的两类问题：

| 诉求 | 典型场景 | 推荐方式 |
| :--- | :--- | :--- |
| **和宿主机工作区协作** | 改配置、看日志、挂源码，两边看同一份文件 | **Bind Mount** |
| **业务数据脱离容器存活** | Redis / MySQL / RabbitMQ 数据目录；换容器仍复用 | **命名卷 Named Volume** |

> 命名卷**不是**「给电脑做磁盘分区」那么简单，更像：  
> **给有状态服务一块 Docker 托管的数据盘，生命周期跟卷名走，不跟容器 ID 走。**

---

## 二、 三种存储位置对比

| 存哪 | `docker rm` 之后 | 谁管路径 | `volume ls` 可见 |
| :--- | :--- | :--- | :--- |
| 容器可写层（不挂载） | 数据没了 | 容器自己 | 否 |
| **命名卷** `-v redis-data:/data` | **数据还在** | Docker | 是（可读名字） |
| **匿名卷**（哈希名） | 数据还在，但难认难管 | Docker | 是（一长串哈希） |
| **Bind Mount** `-v /宿主机路径:/容器路径` | 数据在宿主机目录里 | 你自己 | **否** |

---

## 三、 `-v` 同一个旗，两种语义

历史原因：早期把「挂一块存储进容器」都叫 volume，所以共用 `-v`。  
Docker 靠**冒号左边**判断类型：

```text
-v <左边>:<容器内路径>
```

| 左边长什么样 | 类型 | 示例 |
| :--- | :--- | :--- |
| 短名字（无 `/`） | **命名卷** | `-v redis-data:/data` |
| 绝对路径 / `~` | **Bind Mount** | `-v ~/proj/docker/data:/host-data` |
| 省略左边 `-v /data` | **匿名卷** | 不推荐手写 |

### 现代写法：`--mount`（类型写死，无歧义）

```bash
# 命名卷
--mount type=volume,source=redis-data,target=/data

# 绑定挂载
--mount type=bind,source=/Users/mac/.../docker/data,target=/host-data
```

日常练手 `-v` 即可；生产/复杂挂载更推荐 `--mount`。

### 一条 `run` 可以挂多次、混用

```bash
docker run -d --name lredis \
  -p 6379:6379 \
  -v redis-data:/data \
  -v /Users/mac/.../docker/data:/host-data \
  redis:7-alpine
```

`inspect` 里会看到多条 `Mounts`，`Type` 分别为 `volume` / `bind`。

---

## 四、 命名卷：到底有什么价值？

相对 Bind，命名卷主要赢在：

1. **可移植**：写法是 `redis-data:/data`，不写死本机绝对路径；换机器/CI 更稳。
2. **托管与隔离**：数据放在 Docker 管理的 volumes 下，不和项目源码目录搅在一起；中间件用户权限更省心。
3. **容器可重建**：`rm` 旧容器 → `run` 新容器挂**同名卷** → 数据接着用（升级小版本、换参数都常用）。
4. **可管理**：`docker volume ls` / `inspect` / 备份；多个服务卷名分开（`redis-data`、`mq-data`）。
5. **Mac Desktop 上**：数据库类数据放命名卷，有时比大量小文件走 bind 更顺（少一层文件共享摩擦）。

### 恰当类比（与不当类比）

- ✅ 像：给进程一块**不会随进程销毁的硬盘目录**；下次新进程再从这个目录读回状态。
- ❌ 不像：Docker 自动帮你「把内存对象序列化」。  
  **应用自己**决定何时写入该目录（Redis 的 RDB/AOF、MySQL 的表文件等）。

---

## 五、 Bind Mount：宿主机路径 ↔ 容器路径

本质是**两边看同一份文件**，不是单向「往外暴露」。

```bash
mkdir -p ~/docker-learn/redis-bind
echo "hello-from-host" > ~/docker-learn/redis-bind/note.txt

docker run --rm -it \
  -v ~/docker-learn/redis-bind:/host-data \
  redis:7-alpine sh

# 容器内
ls /host-data
cat /host-data/note.txt
```

### 经典踩坑：把文件挂成了「目录名」

```bash
# 错：宿主机是文件 note.txt → 容器里 /host-data 变成文件，不能 cd
-v ~/docker-learn/redis-bind/note.txt:/host-data

# 对：目录挂目录
-v ~/docker-learn/redis-bind:/host-data
```

`inspect` / `ls -l` 看首字符：`-` 是文件，`d` 是目录。

---

## 六、 匿名卷：能活，但难管

Redis 官方镜像声明了 `VOLUME /data`。  
若启动时**没有**显式 `-v 名字:/data`，Docker 仍会给 `/data` 挂一个**匿名卷**（`Name` 为一长串哈希）。

- 删容器默认不删卷 → 数据可能还在，但你很难记得「哪个哈希是哪次实验」。
- 练习与生产都应显式命名：`-v redis-data:/data`。

判断：

```text
"Type": "volume" + "Name": "redis-data"     → 命名卷
"Type": "volume" + "Name": "e17a1527..."    → 匿名卷
"Type": "bind"   + Source 为本机路径         → 绑定挂载
```

---

## 七、 实战坑：卷挂对了，数据还是丢了（Redis）

现象：`-v redis-data:/data` → `SET` → `docker rm -f` → 同卷重建 → `GET` 为 `(nil)`。  
排查发现卷里没有 `dump.rdb`，且：

```text
save: 3600 1 300 100 60 10000
appendonly: no
```

**原因**：

1. `SET` 只写在 **Redis 内存**；
2. 默认 RDB 不会立刻落盘；AOF 默认关闭；
3. `docker rm -f` **强杀**，不给 Redis 优雅退出时保存的机会。

**正确验证流程**：

```bash
docker exec -it lredis redis-cli SET test 222
docker exec -it lredis redis-cli SAVE          # 强制落盘
docker exec -it lredis ls -la /data           # 应有 dump.rdb

docker stop lredis && docker rm lredis        # 先优雅停止再删

docker run -d --name lredis \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7-alpine

docker exec -it lredis redis-cli GET test     # 应为 "222"
```

学习期也可开 AOF：

```bash
docker run -d --name lredis \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7-alpine \
  redis-server --appendonly yes
```

> **口诀**：挂载保证「磁盘目录还在」；落盘保证「应用状态写进了该目录」。两件事缺一不可。

---

## 八、 常用命令速查

| 意图 | 命令 |
| :--- | :--- |
| 列出卷 | `docker volume ls` |
| 查看卷详情 | `docker volume inspect redis-data` |
| 查看容器挂载 | `docker inspect <容器> --format '{{json .Mounts}}'` |
| 删除未使用卷 | `docker volume prune`（慎用） |
| 删指定卷 | `docker volume rm redis-data`（需无容器引用） |

用临时容器看命名卷内容（不必进业务容器）：

```bash
docker run --rm -v redis-data:/data alpine ls -la /data
```

---

## 九、 选型口诀（够用版）

| 场景 | 用什么 |
| :--- | :--- |
| 源码、配置、要在 IDE 里改 | **Bind Mount** |
| Redis / MySQL / MQ 的数据目录 | **命名卷** |
| 临时练手、随容器扔 | 可不挂；避免依赖匿名卷 |

---

## 十、 与下一阶段的衔接

有了「数据盘」之后，下一个问题是：**多个容器之间怎么互相访问？**  
`-p 6379:6379` 只解决「宿主机访问容器」；容器 A 访问容器 B 的 Redis，要靠 Docker 网络与服务发现——见 `03-container-networking.md`。
