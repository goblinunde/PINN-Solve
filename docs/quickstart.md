# PINN-Solve 快速入门

## 核心功能已实现

### ✅ Rust核心层
- 神经网络前向传播
- 基础自动微分框架
- PDE求解器结构
- Python绑定（PyO3）

### ✅ Python后端
- FastAPI RESTful API
- 训练任务管理
- 结果查询接口
- Rust模块集成

### ✅ Vue3前端
- 问题配置界面
- 实时训练监控
- 3D解可视化（Plotly.js）
- 损失曲线图表

## 使用流程

### 1. 配置问题
访问 http://localhost:38000，在配置页面输入：
- 问题名称
- PDE方程
- 网络结构（如：2,32,32,32,1）
- 训练轮数
- 学习率

### 2. 开始训练
点击"开始训练"按钮，系统会：
- 创建训练任务
- 调用Rust核心进行计算
- 自动跳转到监控页面

### 3. 监控训练
监控页面实时显示：
- 当前损失值
- 训练进度
- 损失曲线图

### 4. 查看结果
训练完成后：
- 点击"查看结果"按钮
- 查看3D解的可视化
- 分析求解质量

## API接口

### 创建训练任务
```bash
curl -X POST http://localhost:8000/api/train/ \
  -H "Content-Type: application/json" \
  -d '{
    "layers": [2, 32, 32, 1],
    "learning_rate": 0.001,
    "epochs": 1000,
    "n_points": 100
  }'
```

### 查询训练状态
```bash
curl http://localhost:8000/api/train/task-1/status
```

### 获取结果
```bash
curl http://localhost:8000/api/results/task-1
```

## 示例问题

### 2D Laplace方程
```
PDE: u_xx + u_yy = 0
域: [0,1] × [0,1]
边界条件: u=0 on boundary
```

配置：
- 网络: 2,32,32,32,1
- 学习率: 0.001
- 训练轮数: 5000

## 下一步开发

1. **完善自动微分**：实现完整的反向传播
2. **PDE残差计算**：支持各类偏微分方程
3. **边界条件处理**：Dirichlet、Neumann等
4. **优化算法**：Adam、L-BFGS
5. **GPU加速**：CUDA支持
6. **更多可视化**：等高线图、误差分析

## 故障排除

### Rust模块未找到
如果后端提示找不到pinn_core模块：
```bash
cd pinn-core
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 cargo build --release
```

### 前端依赖问题
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### 端口占用
修改配置文件中的端口：
- 后端: `backend/main.py` (默认8000)
- 前端: `frontend/vite.config.js` (默认38000)
