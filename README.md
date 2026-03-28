# PINN-Solve

PINN-Solve 是一个面向物理信息神经网络的全栈求解平台。当前版本已经覆盖 Rust 原生求解核心、FastAPI + Celery 后端任务系统，以及支持 PDE 模板和积木式网络搭建的 Vue 前端。

## 当前能力

- Rust `pinn-core` 支持可配置 PINN 求解器
- 支持 `Laplace 2D`、`Poisson 2D`、`Heat 1D`、`Burgers 1D`
- 支持 `Adam`、`SGD` 优化器
- 支持 `tanh`、`relu`、`sigmoid`、`softplus`、`linear` 激活
- 支持隐藏层残差块和前端网络搭建器
- 后端支持任务创建、列表、详情、取消、重试、删除、结果查询
- 支持 worker 心跳、队列概览和 SQLite 持久化

## 技术栈

- 核心计算: Rust + PyO3
- 后端服务: FastAPI + Celery + SQLAlchemy
- 前端界面: Vue 3 + Vite + Plotly
- 默认持久化: SQLite
- 默认任务队列: Celery filesystem broker

## 文档

- 文档导航: [docs/README.md](docs/README.md)
- 快速上手: [docs/quickstart.md](docs/quickstart.md)
- 架构说明: [docs/architecture.md](docs/architecture.md)
- 训练与数据指南: [docs/training-guide.md](docs/training-guide.md)
- 数据库工作台: [docs/database-workspace.md](docs/database-workspace.md)
- 常见问题: [docs/faq.md](docs/faq.md)
- 仓库协作规范: [AGENTS.md](AGENTS.md)

## 项目结构

```text
PINN-Solve/
├── pinn-core/              # Rust PINN 核心、求解器与 PyO3 绑定
├── backend/                # FastAPI API、Celery worker、SQLite 数据
│   ├── api/                # REST 接口
│   ├── services/           # 任务和系统状态服务
│   ├── tasks/              # Celery 任务与运行时配置
│   └── pinn_solve.db       # 任务和 worker 状态数据库
├── frontend/               # Vue 前端
│   ├── src/views/          # 配置、监控、结果、任务中心
│   └── src/api/            # 后端接口封装
├── docs/                   # 架构与快速开始文档
├── Makefile                # 启动、关闭、重启、日志和构建命令
└── start-dev.sh            # 开发态一键启动脚本
```

## 快速开始

### 1. 安装依赖

Rust:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Python:

```bash
pip install uv
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Node.js:

```bash
nvm install node
```

### 2. 一键启动

推荐直接使用 `Makefile`:

```bash
make help
make up
make status
```

常用命令:

```bash
make rust-build
make worker-start
make api-start
make frontend-start
make logs
make down
```

说明:

- `make rust-build` 会同步生成 Python 实际导入的 `pinn_core.so`
- API 默认运行在 `http://localhost:8000`
- 前端默认运行在 `http://localhost:38000`
- 任务、结果和 worker 状态保存在 `backend/pinn_solve.db`

### 3. 手动启动

```bash
cd backend
source .venv/bin/activate
./start-worker.sh
```

新终端:

```bash
cd backend
source .venv/bin/activate
python main.py
```

新终端:

```bash
cd frontend
npm install
npm run dev
```

## 前端使用方式

进入配置页后可以直接:

- 选择 PDE 模板
- 选择优化器和输出激活
- 设置训练轮数、配点数、边界点数和边界损失权重
- 按块添加隐藏层，单独设置宽度、激活和残差连接

训练提交后会进入监控页；任务中心支持搜索、筛选、取消、重试、批量删除，并显示 worker 与队列状态。

## 主要 API

- `GET /api/problems/catalog`: 获取 PDE、优化器、激活函数和网络预设目录
- `POST /api/train/`: 创建训练任务
- `GET /api/train/`: 获取任务列表和计数
- `GET /api/train/{task_id}/status`: 查询任务状态
- `POST /api/train/{task_id}/cancel`: 请求取消任务
- `POST /api/train/{task_id}/retry`: 重试失败或已取消任务
- `GET /api/results/{task_id}`: 获取训练结果
- `GET /api/system/overview`: 获取 worker 和队列概览

## 验证命令

```bash
make rust-build
python -m py_compile $(rg --files backend -g '*.py') test_features.py
cd frontend && npm run build
```

## 当前限制

- 运行中的 Rust 原生训练仍然是协作式取消，不是强制中断
- 默认 broker 为 filesystem，适合本地开发；生产部署建议替换为 Redis
- 当前 PDE 与边界条件仍以内置模板为主，自定义表达式能力还可以继续扩展

## 许可证

MIT
