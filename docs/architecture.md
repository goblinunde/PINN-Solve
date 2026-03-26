# PINN-Solve 开发文档

## 架构说明

### 1. Rust核心层 (pinn-core)

负责高性能数值计算，包括：
- 自动微分引擎
- 神经网络前向/反向传播
- PDE残差计算
- 优化算法

### 2. Python后端层 (backend)

提供API服务和任务调度：
- FastAPI RESTful接口
- Celery异步任务队列
- 数据库管理
- 数据预处理和后处理

### 3. Vue前端层 (frontend)

用户交互界面：
- 问题配置表单
- 训练过程监控
- 结果可视化
- 历史记录管理

## API接口

### 创建问题
```
POST /api/problems/
Body: {问题配置JSON}
```

### 启动训练
```
POST /api/train/
Body: {训练配置}
```

### 查询状态
```
GET /api/train/{task_id}/status
```

### 获取结果
```
GET /api/results/{task_id}
```

## 数据流

1. 前端提交配置 → FastAPI
2. FastAPI验证并创建任务 → Celery
3. Celery调用Rust核心 → PyO3绑定
4. 训练过程通过WebSocket推送进度
5. 结果存储到数据库
6. 前端获取并可视化结果

## 开发指南

### 添加新的PDE类型

1. 在 `pinn-core/src/solver/` 添加求解器
2. 在 `backend/preprocessing/` 添加预处理逻辑
3. 在 `frontend/src/components/` 添加配置界面

### 添加新的可视化

1. 在 `frontend/src/visualization/` 创建组件
2. 使用Plotly.js或Three.js实现
3. 在结果页面引入组件
