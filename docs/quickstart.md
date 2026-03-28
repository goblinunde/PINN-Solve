# PINN-Solve 快速开始

本文档用于帮助你在一台本地开发机上完成首次运行，包括依赖安装、CPU/GPU 依赖选择、服务启动、第一次训练，以及数据库工作台的基本使用。

## 1. 环境要求

建议准备以下环境:

- Rust stable
- Python 3.10+
- Node.js 18+
- MySQL 8.x，若要使用数据库工作台

项目目录结构中的关键部分:

- `pinn-core/`: Rust 求解核心与 PyO3 绑定
- `backend/`: FastAPI、Celery、数据模型和服务
- `frontend/`: Vue 3 + Vite 前端
- `docs/`: 项目文档

## 2. 安装依赖

### Rust

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Python 后端

进入后端目录后，使用项目提供的依赖安装脚本:

```bash
cd backend
./install-deps.sh auto
```

可选模式:

- `./install-deps.sh auto`
  自动检查是否存在 `nvidia-smi`
- `./install-deps.sh cpu`
  强制安装 CPU 版 PyTorch，适合没有 NVIDIA 显卡的机器
- `./install-deps.sh gpu`
  安装 GPU 版 PyTorch，适合有 CUDA 环境的机器

说明:

- 基础依赖包含 `fastapi`、`celery`、`sqlalchemy`、`pymysql`、`sshtunnel` 等
- 如果只执行 `pip install -r requirements.txt`，当前只会安装基础依赖，不会自动装 PyTorch

### Node.js 前端

```bash
cd frontend
npm install
```

## 3. 构建 Rust 扩展

如果你需要启用 Rust 原生求解器，或启用 Rust 管理数据库密码/密钥，需要先构建扩展:

```bash
cd pinn-core
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 cargo build --release
```

如果你主要依赖 Python/Torch 后端训练，Rust 扩展暂时不可用时系统也能运行，但会走 Python 回退路径。

## 4. 启动开发环境

### 方式 A: 使用 Makefile

```bash
make up
make status
```

默认地址:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Frontend: `http://localhost:38000`

### 方式 B: 手动启动

终端 1:

```bash
cd backend
source .venv/bin/activate
python -m celery -A tasks.celery_app worker --pool solo --loglevel INFO
```

终端 2:

```bash
cd backend
source .venv/bin/activate
python main.py
```

终端 3:

```bash
cd frontend
npm run dev
```

## 5. 校验环境是否正常

### 检查 API

```bash
curl http://localhost:8000/health
```

如果安装了 PyTorch，返回结果中会包含 `torch_runtime`，例如:

```json
{
  "status": "ok",
  "database_backend": "sqlite",
  "torch_runtime": {
    "available": true,
    "device": "cpu",
    "cuda_available": false,
    "requested_device": "cpu"
  }
}
```

### 检查数据库工作台路由

```bash
curl http://localhost:8000/api/db/profiles
```

正常情况下应返回:

```json
{"items":[]}
```

### 检查前端构建

```bash
cd frontend
npm run build
```

## 6. 第一次训练

前端配置页支持选择:

- PDE 模板: `Laplace 2D`、`Poisson 2D`、`Heat 1D`、`Burgers 1D`
- 优化器: `Adam`、`SGD`
- 网络结构: `mlp`、`cnn`、`rnn`、`gru`、`lstm`
- 每层隐藏块的宽度、激活和残差开关

训练流程:

1. 打开前端配置页
2. 设置训练轮数、采样点数、边界点数和学习率
3. 选择 PDE 模板和网络结构
4. 点击“开始训练”
5. 在监控页查看进度和损失
6. 在结果页查看数值结果和图表

说明:

- 若 Rust `pinn_core` 可用，优先走 Rust 原生训练
- 若 Rust 模块不可用且已安装 PyTorch，则回退到 Python/Torch 训练
- 若两者都不可用，系统只能生成模拟数据

## 7. 配置 MySQL 持久化

默认后端持久化可以使用 SQLite。若要改成 MySQL，请先创建数据库:

```sql
CREATE DATABASE PINNSOLVER CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

然后在 `backend/.env` 中配置:

```env
PINNSOLVER_DB_BACKEND=mysql
PINNSOLVER_DB_HOST=127.0.0.1
PINNSOLVER_DB_PORT=3306
PINNSOLVER_DB_USER=root
PINNSOLVER_DB_PASSWORD=your_password
PINNSOLVER_DB_NAME=PINNSOLVER
PINNSOLVER_TORCH_DEVICE=cpu
```

配置完成后重启后端。

## 8. 使用数据库工作台

数据库工作台入口位于前端导航栏，可完成:

- 保存 MySQL 连接
- 测试连接
- 浏览数据库和表
- 创建数据库
- 创建表
- 插入 JSON 行数据
- 粘贴 CSV 导入
- 使用 SSH 隧道连接云端 SQL 服务

如果启用了 `Save password`，后端会尝试通过 Rust 层加密保存数据库口令和 SSH 敏感字段。

## 9. 常用验证命令

```bash
python -m compileall backend
cd frontend && npm run build
cd pinn-core && PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 cargo check
```

## 10. 下一步阅读

- [架构说明](./architecture.md)
- [训练与数据指南](./training-guide.md)
- [数据库工作台](./database-workspace.md)
- [常见问题](./faq.md)
