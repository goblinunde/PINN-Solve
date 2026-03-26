# PINN-Solve 快速开始

## 1. 依赖准备

### Rust

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Python

```bash
pip install uv
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Node.js

```bash
nvm install node
```

## 2. 启动整套开发环境

推荐使用根目录 `Makefile`:

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

默认地址:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Frontend: `http://localhost:38000`

说明:

- `make rust-build` 会构建 Rust 核心，并同步生成 Python 导入所需的 `pinn_core.so`
- Celery 使用 filesystem broker，任务状态和结果持久化在 `backend/pinn_solve.db`

## 3. 手动启动方式

终端 1:

```bash
cd backend
source .venv/bin/activate
./start-worker.sh
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
npm install
npm run dev
```

## 4. 第一次训练

访问前端配置页后，可以直接:

- 选择 PDE 模板: `Laplace 2D`、`Poisson 2D`、`Heat 1D`、`Burgers 1D`
- 选择优化器: `Adam` 或 `SGD`
- 设置训练轮数、配点数、边界点数、边界损失权重
- 使用网络搭建器添加隐藏层块，并为每个块设置宽度、激活函数和残差连接

点击“开始训练”后:

1. 前端调用 `POST /api/train/`
2. 后端创建持久化任务并投递 Celery
3. 监控页轮询显示进度和损失
4. 训练完成后结果页展示 3D 解网格

任务中心还支持:

- 搜索和筛选任务
- 查看 worker 在线状态
- 查看队列概览
- 取消、重试、删除和批量删除任务

## 5. API 示例

### 获取问题目录

```bash
curl http://localhost:8000/api/problems/catalog
```

### 创建带 `solver_config` 的训练任务

```bash
curl -X POST http://localhost:8000/api/train/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Heat demo",
    "epochs": 200,
    "n_points": 128,
    "n_boundary": 64,
    "solver_config": {
      "network": {
        "input_dim": 2,
        "hidden_layers": [
          { "size": 32, "activation": "tanh", "residual": false },
          { "size": 32, "activation": "softplus", "residual": true }
        ],
        "output_dim": 1,
        "output_activation": "linear"
      },
      "optimizer": "adam",
      "learning_rate": 0.001,
      "pde": {
        "kind": "heat_1d",
        "source_type": "zero",
        "alpha": 0.1,
        "viscosity": 0.01
      },
      "epsilon": 0.0001,
      "lambda_boundary": 10.0,
      "collocation_batch_size": 64
    }
  }'
```

### 查询任务状态

```bash
curl http://localhost:8000/api/train/<task_id>/status
```

### 查询系统概览

```bash
curl http://localhost:8000/api/system/overview
```

### 获取结果

```bash
curl http://localhost:8000/api/results/<task_id>
```

## 6. 验证

```bash
make rust-build
python -m py_compile $(rg --files backend -g '*.py') test_features.py
cd frontend && npm run build
```

## 7. 故障排除

### Rust 模块未生效

如果后端仍然加载旧版 `pinn_core.so`:

```bash
make rust-build
```

不要只执行裸 `cargo build --release`，因为 Python 实际导入的动态库需要同步。

### 任务一直停在 queued

通常表示 worker 未启动或没有心跳:

```bash
make worker-start
make logs-worker
```

也可以直接查看 `GET /api/system/overview`。

### 前端依赖或构建异常

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### 端口冲突

可以通过 `make` 变量覆写端口:

```bash
make frontend-start FRONTEND_PORT=39000
make api-start API_PORT=8100
```
