# Makefile 使用说明

`Makefile` 是本项目本地开发的统一入口，适合在不记忆长命令的情况下完成 Rust 构建、后端启动、前端启动、日志查看和运行状态管理。

## 适用场景

- 第一次启动整套开发环境
- 单独重启 API、Celery worker 或前端
- 查看 PID 和日志
- 清理本地运行时文件

## 快速命令

```bash
make help
make up
make status
make logs
make down
```

## 命令总览

### Rust 核心

```bash
make rust-build
make rust-clean
make rust-rebuild
make rust-status
```

说明:

- `make rust-build` 会在 `pinn-core/` 下执行 `cargo build --release`
- 构建结束后会把可供 Python 导入的动态库同步为 `pinn_core.so`
- 如果你修改了 Rust 求解器、绑定层或密钥管理逻辑，先执行这一组命令

### 后端服务

```bash
make worker-start
make worker-stop
make worker-restart
make worker-status

make api-start
make api-stop
make api-restart
make api-status
```

说明:

- `worker` 负责异步训练任务
- `api` 负责 FastAPI 接口与数据库工作台接口
- 两者都会把日志写到根目录 `logs/`

### 前端服务

```bash
make frontend-start
make frontend-stop
make frontend-restart
make frontend-status
```

说明:

- 前端默认运行在 `http://127.0.0.1:38000`
- 如果你在局域网内调试，可以覆写 host 或 port

### 一键命令

```bash
make up
make down
make restart
make status
```

说明:

- `make up` 会按顺序执行 `rust-build`、`worker-start`、`api-start`、`frontend-start`
- `make down` 会关闭前端、API 和 worker
- `make restart` 适合切换依赖或环境变量后统一重启

### 日志与运行时

```bash
make logs
make logs-api
make logs-worker
make logs-frontend
make clean-runtime
```

说明:

- PID 文件在 `.run/`
- 日志文件在 `logs/`
- `clean-runtime` 会删除 PID 和日志文件，但不会删除数据库或源码

## 端口覆写

默认端口:

- API: `8000`
- Frontend: `38000`

可以在命令后覆盖:

```bash
make api-start API_PORT=8100
make frontend-start FRONTEND_PORT=39000
make up API_PORT=8100 FRONTEND_PORT=39000
```

## 常见使用组合

### 重新编译 Rust 后重启后端

```bash
make rust-build
make api-restart
make worker-restart
```

### 只调前端样式

```bash
make frontend-start
make logs-frontend
```

### 查看某个组件是否真正启动

```bash
make status
```

如果某个服务显示 `stopped`，优先查看对应日志:

```bash
make logs-api
make logs-worker
make logs-frontend
```
