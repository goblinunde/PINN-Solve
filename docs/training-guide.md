# 训练与数据指南

本文档说明当前版本中训练任务的配置方式、网络结构选择、运行模式和数据集导入能力。

## 1. 训练任务由什么组成

一次训练请求通常包括两部分:

- 任务元数据
  例如任务名称、训练轮数、采样点数、边界点数
- `solver_config`
  例如网络结构、PDE 类型、优化器、学习率和边界损失权重

## 2. 当前支持的 PDE

- `laplace_2d`
- `poisson_2d`
- `heat_1d`
- `burgers_1d`

这些模板可从 `GET /api/problems/catalog` 获取。

## 3. 当前支持的网络结构

训练后端已经扩展为支持:

- `mlp`
- `cnn`
- `rnn`
- `gru`
- `lstm`

说明:

- `mlp` 适合通用 PDE 近似
- `cnn` 更适合具有网格感的数据输入
- `rnn`、`gru`、`lstm` 更适合时间序列或序列化输入

## 4. 隐藏层与残差连接

当前配置允许你为隐藏层块设置:

- `size`
- `activation`
- `residual`

残差连接的意义:

- 减少深层网络训练退化
- 提升梯度传播稳定性
- 让更深的网络更容易收敛

## 5. 训练后端选择逻辑

系统训练时会按以下顺序尝试:

1. Rust `pinn_core`
2. Python/Torch
3. 模拟数据

这意味着:

- Rust 可用时优先走高性能原生后端
- Rust 不可用但安装了 PyTorch 时，训练仍能继续
- 两者都不可用时，前端仍能拿到结构化的模拟结果用于联调

## 6. CPU/GPU 选择

通过环境变量控制:

```env
PINNSOLVER_TORCH_DEVICE=cpu
```

可选值:

- `cpu`
- `cuda`
- `auto`

建议:

- 无 NVIDIA 显卡的机器固定为 `cpu`
- 有 CUDA 环境的机器用 `auto` 或 `cuda`

## 7. 训练请求示例

```bash
curl -X POST http://localhost:8000/api/train/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Heat Builder Validation",
    "epochs": 200,
    "n_points": 256,
    "n_boundary": 64,
    "solver_config": {
      "network": {
        "architecture": "mlp",
        "input_dim": 2,
        "hidden_layers": [
          { "size": 64, "activation": "tanh", "residual": false },
          { "size": 64, "activation": "tanh", "residual": true }
        ],
        "output_dim": 1,
        "output_activation": "linear"
      },
      "optimizer": "adam",
      "learning_rate": 0.001,
      "pde": {
        "kind": "heat_1d",
        "alpha": 0.2
      },
      "lambda_boundary": 10.0,
      "collocation_batch_size": 64
    }
  }'
```

## 8. 数据集导入接口

当前后端提供了一个独立的数据集导入接口:

- `POST /api/datasets/import`
- `GET /api/datasets/`
- `GET /api/datasets/{dataset_id}`

请求示例:

```bash
curl -X POST http://localhost:8000/api/datasets/import \
  -H "Content-Type: application/json" \
  -d '{
    "name": "heat-observations",
    "pde_kind": "heat_1d",
    "description": "simple supervised samples",
    "inputs": [[0.0, 0.0], [0.1, 0.0], [0.2, 0.1]],
    "targets": [1.0, 0.8, 0.65],
    "metadata": {
      "split": "train",
      "source": "manual"
    }
  }'
```

## 9. 当前数据集能力边界

目前已经完成的是:

- 数据集导入
- 数据集持久化
- 数据集详情查询

尚未完全完成的是:

- 从数据库工作台直接选表并喂给训练器
- 数据监督项自动加入 PINN 损失
- 数据集切分策略的前端可视化配置

## 10. 监控与结果查看

训练过程中，前端可以看到:

- 任务状态
- 当前损失
- 训练进度
- 执行模式

训练完成后，结果页和历史页可查看:

- 损失曲线
- 解的可视化
- 历史任务记录

## 11. 推荐训练流程

1. 先从内置 PDE 模板开始验证整条链路
2. 用 `mlp + tanh` 作为基础基线
3. 如果网络较深，再逐步加入残差连接
4. 需要监督数据时，先把样本导入数据库或数据集接口
5. 稳定后再尝试 `cnn`、`rnn`、`gru`、`lstm`
