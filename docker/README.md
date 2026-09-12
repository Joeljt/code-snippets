# Docker 学习指南与实践路线

本项目作为后端中间件与基础架构演进的基石，与 `rabbitmq/` 同级。目标是以**「够用、好用、不堆砌理论」**为原则，快速建立容器化思维，支撑后续 Redis、RabbitMQ、MySQL 等中间件与微服务 Demo 的敏捷搭建。

---

## 🗺️ 学习路线与知识地图

```text
docker/
├── README.md                           # 本指南：路线图与模块索引
├── docs/                               # 核心技术文档与概念笔记
│   ├── 01-image-and-container-basics.md # 镜像与容器基石（生命周期、Tag策略、Alpine原理、选型）
│   ├── 02-storage-and-volumes.md       # 【下一阶段】存储与持久化（Volume vs Bind Mount、权限、数据解耦）
│   ├── 03-container-networking.md      # 容器网络通信（Bridge 网络、端口映射、容器间 DNS 解析）
│   ├── 04-dockerfile-and-images.md     # 镜像构建进阶（Dockerfile 指令、分层缓存、多阶段构建）
│   └── 05-docker-compose.md            # 多服务编排（Compose 语法、依赖定义、一键环境搭建）
└── demos/                              # 实战靶场（配合各阶段的小型验证项目）
```

---

## 🧭 各阶段核心目标

| 阶段 | 模块 | 核心解决问题 | 状态 |
| :--- | :--- | :--- | :--- |
| **阶段 1** | **[镜像与容器基石](docs/01-image-and-container-basics.md)** | 理解镜像分层、容器生命周期、`run` 与 `start` 边界、Tag 策略、Alpine 原理 | ✅ 已完成并沉淀 |
| **阶段 2** | **数据持久化 (Storage & Volume)** | 搞懂为什么删容器数据会丢、命名卷 (Named Volume) vs 绑定挂载 (Bind Mount) 场景与实战 | 🔄 进行中 |
| **阶段 3** | **网络通信 (Networking)** | 容器内如何互通、服务名自动解析、端口映射机制（为什么不能只靠 localhost） | ⏳ 规划中 |
| **阶段 4** | **Dockerfile 镜像构建** | 编写高质量 Dockerfile、层缓存优化技巧、Alpine/Slim 选型踩坑与规避 | ⏳ 规划中 |
| **阶段 5** | **Docker Compose 编排** | 用声明式配置替代冗长的 run 命令，一键拉起「Redis + RabbitMQ + Web 业务应用」 | ⏳ 规划中 |
