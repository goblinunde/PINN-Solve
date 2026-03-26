# PINN-Solve 软件设计规划

## 项目概述

物理信息神经网络(Physics-Informed Neural Networks, PINN)求解软件，用于求解偏微分方程(PDE)问题。

**技术栈:**
- 核心计算: Rust (高性能数值计算)
- 后端接口: Python (科学计算生态集成)
- 前端展示: Vue 3 + CSS

---

## 架构设计

### 1. 整体架构

```
┌─────────────────────────────────────────┐
│         前端层 (Vue 3)                   │
│  - 可视化界面                            │
│  - 参数配置                              │
│  - 结果展示                              │
└──────────────┬──────────────────────────┘
               │ HTTP/WebSocket
┌──────────────▼──────────────────────────┐
│      后端API层 (Python/FastAPI)          │
│  - RESTful API                          │
│  - 任务调度                              │
│  - 数据预处理                            │
└──────────────┬──────────────────────────┘
               │ FFI (PyO3)
┌──────────────▼──────────────────────────┐
│      核心计算层 (Rust)                   │
│  - PINN模型训练                          │
│  - 自动微分                              │
│  - 数值求解器                            │
│  - GPU加速                               │
└─────────────────────────────────────────┘
```

---

## 模块划分

### Rust 核心层 (`pinn-core/`)

#### 1.1 自动微分模块 (`autodiff/`)
- 计算图构建
- 前向/反向传播
- 梯度计算

#### 1.2 神经网络模块 (`nn/`)
- 全连接层
- 激活函数 (tanh, sigmoid, ReLU, GELU)
- 权重初始化策略
- 优化器 (Adam, L-BFGS)

#### 1.3 PDE求解器 (`solver/`)
- 损失函数计算 (PDE残差 + 边界条件 + 初始条件)
- 采样策略 (均匀采样、自适应采样)
- 训练循环
- 收敛判断

#### 1.4 数值计算 (`numerics/`)
- 矩阵运算
- 线性代数求解
- 插值与积分

#### 1.5 GPU加速 (`gpu/`)
- CUDA/ROCm支持
- Tensor操作加速

#### 1.6 Python绑定 (`bindings/`)
- PyO3接口封装
- 数据类型转换

---

### Python 后端层 (`backend/`)

#### 2.1 API服务 (`api/`)
- FastAPI框架
- 路由定义
  - `/api/problems` - 问题配置
  - `/api/train` - 训练任务
  - `/api/results` - 结果查询
  - `/api/visualize` - 可视化数据

#### 2.2 任务管理 (`tasks/`)
- Celery异步任务队列
- 训练任务调度
- 进度追踪

#### 2.3 数据层 (`data/`)
- 数据库模型 (SQLAlchemy)
- 问题配置存储
- 训练历史记录

#### 2.4 预处理 (`preprocessing/`)
- 几何域定义
- 边界条件解析
- 数据归一化

#### 2.5 后处理 (`postprocessing/`)
- 结果插值
- 误差分析
- 导出功能 (VTK, CSV)

---

### Vue 3 前端层 (`frontend/`)

#### 3.1 页面组件 (`views/`)
- **问题配置页** - PDE方程输入、域定义、边界条件
- **训练监控页** - 实时损失曲线、训练进度
- **结果展示页** - 解的可视化、误差分析
- **历史记录页** - 已完成任务列表

#### 3.2 核心组件 (`components/`)
- **方程编辑器** - LaTeX公式输入
- **几何编辑器** - 2D/3D域绘制
- **图表组件** - 损失曲线、等高线图、3D曲面
- **参数面板** - 网络结构、训练参数配置

#### 3.3 状态管理 (`store/`)
- Pinia状态管理
- 问题配置状态
- 训练状态
- 用户设置

#### 3.4 可视化 (`visualization/`)
- Plotly.js / Three.js
- 2D等高线图
- 3D曲面图
- 动画播放

---

## 技术选型

### Rust依赖
```toml
[dependencies]
ndarray = "0.15"           # 数组计算
nalgebra = "0.32"          # 线性代数
rayon = "1.7"              # 并行计算
pyo3 = "0.20"              # Python绑定
serde = "1.0"              # 序列化
candle-core = "0.3"        # 深度学习框架(可选)
```

### Python依赖
```
fastapi
uvicorn
celery
redis
sqlalchemy
numpy
scipy
matplotlib
pydantic
```

### 前端依赖
```json
{
  "vue": "^3.4",
  "pinia": "^2.1",
  "vue-router": "^4.2",
  "axios": "^1.6",
  "plotly.js": "^2.27",
  "three": "^0.160",
  "katex": "^0.16"
}
```

---

## 数据流设计

### 训练流程
1. 用户在前端配置PDE问题 → Vue表单
2. 提交配置 → FastAPI接收并验证
3. 创建训练任务 → Celery异步队列
4. 调用Rust核心 → PyO3绑定
5. 训练过程 → WebSocket实时推送损失
6. 训练完成 → 结果存储数据库
7. 前端展示 → 可视化组件渲染

### 数据格式
```python
# 问题配置
{
  "pde": "u_xx + u_yy = 0",  # 拉普拉斯方程
  "domain": {"x": [0, 1], "y": [0, 1]},
  "boundary_conditions": [
    {"type": "dirichlet", "location": "x=0", "value": "0"},
    {"type": "dirichlet", "location": "x=1", "value": "sin(pi*y)"}
  ],
  "network": {
    "layers": [2, 50, 50, 50, 1],
    "activation": "tanh"
  },
  "training": {
    "epochs": 10000,
    "lr": 0.001,
    "n_collocation": 10000,
    "n_boundary": 400
  }
}
```

---

## 目录结构

```
PINN-Solve/
├── pinn-core/              # Rust核心
│   ├── src/
│   │   ├── autodiff/
│   │   ├── nn/
│   │   ├── solver/
│   │   ├── numerics/
│   │   ├── gpu/
│   │   └── lib.rs
│   ├── Cargo.toml
│   └── tests/
├── backend/                # Python后端
│   ├── api/
│   ├── tasks/
│   ├── data/
│   ├── preprocessing/
│   ├── postprocessing/
│   ├── requirements.txt
│   └── main.py
├── frontend/               # Vue前端
│   ├── src/
│   │   ├── views/
│   │   ├── components/
│   │   ├── store/
│   │   ├── visualization/
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
├── docs/                   # 文档
├── examples/               # 示例问题
└── README.md
```

---

## 开发阶段

### Phase 1: 核心功能 (4-6周)
- [ ] Rust自动微分引擎
- [ ] 基础神经网络实现
- [ ] 简单PDE求解器 (1D问题)
- [ ] Python绑定

### Phase 2: 后端服务 (3-4周)
- [ ] FastAPI框架搭建
- [ ] 任务队列集成
- [ ] 数据库设计
- [ ] RESTful API实现

### Phase 3: 前端界面 (4-5周)
- [ ] Vue项目初始化
- [ ] 问题配置界面
- [ ] 训练监控界面
- [ ] 可视化组件

### Phase 4: 高级特性 (持续)
- [ ] GPU加速
- [ ] 自适应采样
- [ ] 多维问题支持
- [ ] 预训练模型库
- [ ] 并行训练

---

## 性能目标

- 1D问题求解: < 10秒
- 2D问题求解: < 5分钟
- 3D问题求解: < 30分钟
- 支持10万+配点
- GPU加速提升: 10-50x

---

## 测试策略

### Rust层
- 单元测试: 每个模块独立测试
- 基准测试: 性能回归检测
- 集成测试: 端到端求解验证

### Python层
- API测试: pytest + httpx
- 任务测试: Celery worker测试

### 前端层
- 组件测试: Vitest
- E2E测试: Playwright

---

## 部署方案

### 开发环境
- Docker Compose一键启动
- 热重载支持

### 生产环境
- Rust编译为动态库
- Python打包为wheel
- 前端构建静态文件
- Nginx反向代理
- Redis消息队列
- PostgreSQL数据库

---

## 扩展性考虑

1. **插件系统**: 支持自定义PDE类型
2. **模型市场**: 预训练模型分享
3. **云计算**: 支持分布式训练
4. **多物理场**: 耦合问题求解
5. **优化算法**: 集成更多优化器

---

## 参考资源

- [Physics-Informed Neural Networks (Raissi et al., 2019)](https://www.sciencedirect.com/science/article/pii/S0021999118307125)
- [DeepXDE框架](https://github.com/lululxvi/deepxde)
- [PyO3文档](https://pyo3.rs/)
- [Vue 3文档](https://vuejs.org/)
