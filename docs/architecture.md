# PINN-Solve 架构说明

本文档描述当前仓库的核心模块、运行路径、训练回退机制、数据库工作台和安全敏感信息的处理方式。

## 1. 总体结构

项目由 4 个主要部分构成:

1. `pinn-core/`
   Rust 原生求解核心，负责数值计算、网络结构、自动微分和 PyO3 绑定。
2. `backend/`
   FastAPI 提供 REST API，Celery worker 执行异步训练任务，SQLAlchemy 负责持久化。
3. `frontend/`
   Vue 3 + Vite 前端，负责参数配置、任务监控、结果展示和数据库工作台。
4. `docs/`
   项目文档、操作指南和排障说明。

## 2. 模块职责

### Rust 核心

主要目录:

- `pinn-core/src/autodiff`
- `pinn-core/src/nn`
- `pinn-core/src/numerics`
- `pinn-core/src/solver`
- `pinn-core/src/gpu`
- `pinn-core/src/bindings`

职责:

- 定义 PINN 网络结构
- 计算 PDE 残差和边界损失
- 执行优化器更新
- 暴露 Python 可调用接口
- 管理部分密钥加密/解密能力

### 后端

主要目录:

- `backend/api`
- `backend/services`
- `backend/tasks`
- `backend/data`

职责:

- 接收前端训练请求
- 管理训练任务生命周期
- 根据运行环境选择 Rust 或 Python/Torch 后端
- 管理数据库工作台接口
- 管理训练数据集导入
- 保存任务、结果、连接配置和数据集

### 前端

主要目录:

- `frontend/src/views`
- `frontend/src/components`
- `frontend/src/router`
- `frontend/src/store`
- `frontend/src/locales`

职责:

- 配置 PDE 和网络结构
- 监控训练进度
- 展示损失曲线和结果图
- 管理数据库连接、建库建表和数据导入

## 3. 训练请求数据流

训练数据流如下:

1. 前端调用 `GET /api/problems/catalog` 获取 PDE、优化器和激活函数目录
2. 用户在配置页填写训练参数与 `solver_config`
3. 前端调用 `POST /api/train/`
4. 后端将任务写入 `training_jobs`
5. Celery worker 读取任务并选择训练后端
6. 训练过程持续写回进度、损失和结果
7. 前端监控页和结果页通过轮询刷新显示

## 4. 训练后端选择策略

训练执行链路不是单一路径，而是按优先级回退:

1. Rust `pinn_core`
2. Python/Torch
3. 模拟数据

行为说明:

- Rust 模块可用时，优先使用 Rust 原生求解
- Rust 模块不可用时，尝试使用 `backend/tasks/torch_backend.py`
- 若 PyTorch 也不可用，则返回模拟训练数据，避免前端完全中断

## 5. CPU/GPU 运行策略

后端通过 `PINNSOLVER_TORCH_DEVICE` 控制运行设备:

- `cpu`
- `cuda`
- `auto`

运行时状态可通过 `GET /health` 查看，返回值中包含:

- `torch_runtime.available`
- `torch_runtime.device`
- `torch_runtime.cuda_available`
- `torch_runtime.requested_device`

这套设计用于适配两类机器:

- 无 NVIDIA 显卡的开发机，固定 CPU
- 有 NVIDIA 显卡且装好 CUDA 的训练机，优先 GPU

## 6. 数据存储结构

当前后端支持两种主持久化后端:

- SQLite
- MySQL

主要模型包括:

- `training_jobs`
  训练任务、进度、损失、结果和取消状态
- `worker_states`
  worker 心跳和在线状态
- `db_connection_profiles`
  数据库工作台的连接配置
- `training_datasets`
  导入的数据集

## 7. 数据库工作台架构

数据库工作台的接口前缀为 `/api/db`，支持:

- 保存连接配置
- 测试连接
- 读取 schema
- 创建数据库
- 创建表
- 插入 JSON 行数据
- 导入 CSV 数据

支持两类连接:

- 本地 MySQL 直连
- 通过 SSH 隧道连接云端 MySQL

后端主要由 `backend/services/db_workspace.py` 提供数据库连接、建库建表和数据写入能力。

## 8. 密码与密钥处理

数据库工作台支持保存:

- 数据库密码
- SSH 密码
- SSH 私钥口令

设计原则:

- 前端不回显已保存口令
- 保存时由后端调用 Rust 加密逻辑
- 连接数据库时再短暂解密
- 主密钥保存在本机，不经由前端暴露

这不是完整的密钥托管系统，但比明文持久化更安全。

## 9. 前后端通信方式

当前前端与后端的交互以 HTTP 轮询为主。

说明:

- 训练监控页没有 WebSocket 推送
- 长任务状态通过轮询接口刷新
- 这种方式实现简单，但在高频刷新场景下效率一般

## 10. 当前实现边界

当前版本适合本地开发、教学演示和中小规模实验，仍存在以下边界:

- 数据库工作台目前聚焦 MySQL，不是完整 SQL IDE
- 训练数据集已支持导入与存储，但尚未完整打通到所有训练模式
- 任务取消主要是协作式取消
- 默认 Celery broker 仍以本地开发为导向

## 11. 推荐阅读顺序

1. [快速开始](./quickstart.md)
2. [训练与数据指南](./training-guide.md)
3. [数据库工作台](./database-workspace.md)
4. [常见问题](./faq.md)
