# 常见问题

## 1. `No module named 'pymysql'`

说明后端环境没有安装 MySQL 驱动。执行:

```bash
cd backend
./install-deps.sh cpu
```

如果你在有 NVIDIA 的机器上，也可以执行:

```bash
./install-deps.sh auto
```

## 2. 我的电脑没有 NVIDIA 显卡，为什么还在下载 CUDA 包

现在后端依赖已经拆成基础依赖和 PyTorch 运行模式两部分。

推荐安装方式:

```bash
cd backend
./install-deps.sh cpu
```

如果你只执行 `pip install -r requirements.txt`，当前只会安装基础依赖，不会自动装 GPU 版 PyTorch。

## 3. 如何确认当前后端跑在 CPU 还是 GPU

执行:

```bash
curl http://localhost:8000/health
```

查看返回中的 `torch_runtime`:

- `device: cpu`
- `device: cuda`
- `available: false`

## 4. `curl http://localhost:8000/api/db/profiles` 返回 `Not Found`

这是典型的旧后端进程还在占用端口。处理方式:

1. 停掉旧进程
2. 重启当前仓库里的后端
3. 再重新请求该接口

## 5. 前端数据库工作台一直显示错误

优先检查:

- API 是否已经重启
- `pymysql` 是否安装
- MySQL 是否启动
- `PINNSOLVER` 数据库是否存在

创建数据库:

```sql
CREATE DATABASE PINNSOLVER CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 6. `mysql -u root -p "mypassword"` 为什么不对

因为这样会把 `"mypassword"` 识别成数据库名，而不是密码。

正确写法:

```bash
mysql -u root -p
```

然后在提示符里输入密码。

或者:

```bash
mysql -u root -pmypassword
```

但第二种方式不推荐，因为密码会留在 shell 历史中。

## 7. 任务为什么一直显示“取消中”

这通常说明任务已经请求取消，但 worker 没有正常回写最终状态，或者任务在异常中断后残留为孤儿状态。

当前后端已经补了自动修正逻辑，会尝试把失联的 `cancel_requested` 任务收敛到最终状态。

## 8. Rust 模块不可用时还能训练吗

可以，但前提是后端环境里已经安装 PyTorch。

当前训练链路优先级是:

1. Rust `pinn_core`
2. Python/Torch
3. 模拟数据

## 9. 数据库密码会明文保存吗

当前设计不是明文保存优先，而是:

- 勾选 `Save password` 时，尝试走 Rust 层加密
- 前端不回显已保存密码
- 后端只在连接数据库时临时解密

## 10. 为什么 API 启动时报 `address already in use`

说明 `8000` 端口已经被旧进程占用。

可以先找占用进程:

```bash
lsof -i :8000
```

然后关闭旧进程，或改用其他端口启动。

## 11. 为什么前端能打开，但任务没有进度

一般是 worker 没有启动。

执行:

```bash
make worker-start
make worker-status
make logs-worker
```

## 12. 数据集已经导入，为什么还不能直接用于全部训练

当前版本已经支持数据集导入和存储，但“把数据库样本自动接入所有训练损失项”的链路还在逐步补齐中。现阶段更适合先把数据作为持久化样本管理层使用。
