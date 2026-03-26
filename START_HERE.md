# 🚀 PINN-Solve 启动指南

## ✅ 核心功能已完成

PINN-Solve是一个完整的物理信息神经网络求解系统，包含：
- **Rust核心**: 高性能神经网络计算
- **Python后端**: FastAPI REST API服务
- **Vue3前端**: 交互式可视化界面

---

## 📦 快速启动（3步）

### 步骤1: 编译Rust核心
```bash
cd pinn-core
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 cargo build --release
cd ..
```

### 步骤2: 启动后端
```bash
cd backend
source .venv/bin/activate
python main.py
```
✅ 后端运行在: http://localhost:8000
📚 API文档: http://localhost:8000/docs

### 步骤3: 启动前端（新终端）
```bash
cd frontend
npm install
npm run dev
```
✅ 前端运行在: http://localhost:38000

---

## 🎮 使用流程

### 1️⃣ 配置问题
访问 http://localhost:38000

填写表单：
- **问题名称**: 2D Laplace方程
- **PDE方程**: u_xx + u_yy = 0
- **网络结构**: 2,32,32,32,1
- **训练轮数**: 1000
- **学习率**: 0.001

点击 **"开始训练"**

### 2️⃣ 监控训练
自动跳转到监控页面，实时显示：
- 当前损失值
- 训练进度
- 损失曲线图（对数坐标）

### 3️⃣ 查看结果
训练完成后点击 **"查看结果"**
- 3D曲面图可视化
- 可旋转、缩放交互

---

## 🧪 测试API

### 健康检查
```bash
curl http://localhost:8000/health
```

### 启动训练
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

### 查询状态
```bash
curl http://localhost:8000/api/train/task-1/status
```

---

## 📁 项目结构

```
PINN-Solve/
├── pinn-core/              # Rust核心 ⚡
│   ├── src/
│   │   ├── nn/            # 神经网络
│   │   ├── autodiff/      # 自动微分
│   │   ├── solver/        # PDE求解器
│   │   └── bindings/      # Python绑定
│   └── Cargo.toml
│
├── backend/                # Python后端 🐍
│   ├── api/               # REST API
│   ├── main.py            # 入口文件
│   └── requirements.txt
│
├── frontend/               # Vue3前端 🎨
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 可视化组件
│   │   └── router/        # 路由配置
│   └── package.json
│
└── docs/                   # 文档 📚
    ├── quickstart.md
    └── architecture.md
```

---

## 🎯 核心特性

✅ **高性能计算** - Rust实现的神经网络核心  
✅ **实时监控** - 2秒自动刷新训练状态  
✅ **3D可视化** - Plotly.js交互式图表  
✅ **灵活配置** - 自定义网络结构和参数  
✅ **REST API** - 完整的后端接口  
✅ **响应式UI** - Vue 3现代化界面  

---

## 🔧 配置说明

### 端口配置
- **后端**: 8000 (修改 `backend/main.py`)
- **前端**: 38000 (修改 `frontend/vite.config.js`)

### Python虚拟环境
已使用uv创建在 `backend/.venv/`

### Rust编译产物
位于 `pinn-core/target/release/`

---

## 🐛 故障排除

### Rust编译失败
```bash
# 确保设置环境变量
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
cd pinn-core
cargo clean
cargo build --release
```

### Python依赖问题
```bash
cd backend
uv pip install -r requirements.txt
```

### 前端依赖问题
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### 端口被占用
```bash
# 查看端口占用
lsof -i :8000
lsof -i :38000

# 杀死进程
kill -9 <PID>
```

---

## 📚 文档资源

- **README.md** - 项目概述
- **planning.md** - 设计规划
- **DEVELOPMENT_SUMMARY.md** - 开发总结
- **docs/quickstart.md** - 快速入门
- **docs/architecture.md** - 架构文档

---

## 🎊 开始使用

```bash
# 一键启动（推荐）
./start-dev.sh

# 或手动启动（参考上面的3步）
```

访问 http://localhost:38000 开始你的PINN求解之旅！

---

## 💡 示例问题

### 2D Laplace方程
```
PDE: u_xx + u_yy = 0
网络: 2,32,32,32,1
学习率: 0.001
训练轮数: 5000
```

### 1D热传导方程
```
PDE: u_t - alpha * u_xx = 0
网络: 2,32,32,1
学习率: 0.001
训练轮数: 3000
```

---

## 🚀 下一步

查看 `DEVELOPMENT_SUMMARY.md` 了解：
- 已实现的功能
- 技术架构详情
- 后续开发计划

祝使用愉快！🎉
