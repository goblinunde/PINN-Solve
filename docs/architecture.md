# PINN-Solve 架构说明

## 总览

PINN-Solve 目前采用三层结构:

1. `pinn-core/`
   Rust 原生计算核心，负责网络前向/反向传播、优化器更新、PDE 残差计算和 PyO3 绑定。
2. `backend/`
   FastAPI 提供 REST API，Celery worker 负责异步训练任务，SQLite 存储任务与 worker 状态。
3. `frontend/`
   Vue 负责配置、任务中心、监控和结果可视化，前端通过轮询获取训练进度。

## 运行时组件

- `frontend/src/views/ConfigView.vue`
  积木式配置界面，提交 `solver_config`、训练参数和任务元数据。
- `backend/api/training.py`
  训练任务入口，负责兼容旧配置并标准化为统一的 `solver_config`。
- `backend/tasks/celery_app.py`
  Celery worker 入口，调用 Rust 模块执行原生训练，并写回损失、状态和解。
- `backend/services/training_tasks.py`
  统一处理任务创建、序列化、取消、重试、删除和状态统计。
- `backend/services/system_status.py`
  维护 worker 心跳、在线状态和队列概览。
- `pinn-core/src/solver/mod.rs`
  定义 `SolverConfig`、PDE 预设、边界采样、PDE 残差和训练流程。
- `pinn-core/src/nn/mod.rs`
  定义网络层、激活函数、残差块和优化器实现。

## 数据流

1. 前端从 `GET /api/problems/catalog` 拉取 PDE、优化器、激活函数和网络预设。
2. 用户在配置页组装网络并提交 `POST /api/train/`。
3. FastAPI 将配置归一化后持久化到 `training_jobs`，再投递 Celery 任务。
4. Worker 从队列取任务，调用 `pinn_core` 原生求解器训练。
5. 训练状态、损失曲线、结果网格和错误信息持续写回 SQLite。
6. 前端监控页和任务中心通过轮询 `train`、`results`、`system` 接口刷新状态。

说明:

- 当前没有 WebSocket 推送，前端使用定时轮询。
- 取消是协作式取消；如果底层计算仍在执行，需要等当前训练调用返回后才会完成状态落库。

## 后端数据模型

- `training_jobs`
  记录任务配置、状态、进度、损失、解、错误和取消标记。
- `worker_states`
  记录 worker 在线状态、最近心跳、最近任务和错误信息。
- `problems`
  目前保留了问题配置接口，核心训练流主要由 `training_jobs` 驱动。

## 求解器配置模型

训练入口接受两类配置:

- 兼容模式
  `layers + learning_rate + epochs + n_points + n_boundary`
- 新模式
  `solver_config.network / solver_config.optimizer / solver_config.pde / solver_config.lambda_boundary / solver_config.collocation_batch_size`

当前内置能力:

- PDE: `laplace_2d`、`poisson_2d`、`heat_1d`、`burgers_1d`
- Optimizer: `adam`、`sgd`
- Activation: `tanh`、`relu`、`sigmoid`、`softplus`、`linear`
- Network block: 每个隐藏层块可独立设置 `size`、`activation`、`residual`

## 扩展点

### 新增 PDE

1. 在 `pinn-core/src/solver/mod.rs` 增加 `PDEKind` 分支和残差公式。
2. 在 `backend/api/problems.py` 的目录中补充新模板。
3. 前端配置页会自动消费目录接口，大部分情况下无需新增独立页面逻辑。

### 新增优化器或网络能力

1. 在 `pinn-core/src/nn/mod.rs` 增加优化器或激活函数。
2. 在目录接口中补充选项。
3. 前端 builder 会通过接口渲染新的可选项。

### 更换基础设施

- 目前 Celery 使用 filesystem broker，适合本地开发。
- 若要服务化部署，建议替换为 Redis broker，并保留 SQLite 或升级到 PostgreSQL。
