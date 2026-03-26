# PINN-Solve

物理信息神经网络(Physics-Informed Neural Networks)求解软件

## 技术栈

- **核心计算**: Rust (高性能数值计算)
- **后端API**: Python + FastAPI
- **前端界面**: Vue 3 + Vite

## 项目结构

```
PINN-Solve/
├── pinn-core/          # Rust核心计算模块
├── backend/            # Python后端API
│   └── .venv/         # Python虚拟环境
├── frontend/           # Vue 3前端
├── docs/              # 文档
├── examples/          # 示例问题
└── tests/             # 测试
```

## 快速开始

### 1. Rust核心编译

```bash
cd pinn-core
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 cargo build --release
```

### 2. 后端启动

```bash
cd backend
source .venv/bin/activate
python main.py
```

后端运行在 http://localhost:8000
API文档: http://localhost:8000/docs

### 3. 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:38000

### 或使用一键启动脚本

```bash
./start-dev.sh
```

## 功能特性

- ✅ Rust高性能神经网络核心
- ✅ Python FastAPI后端服务
- ✅ Vue 3响应式前端界面
- ✅ 实时训练监控
- ✅ 3D解可视化
- ✅ 损失曲线图表

## 开发状态

- [x] 项目框架搭建
- [x] Rust核心实现（基础版）
- [x] Python绑定
- [x] API接口完善
- [x] 前端界面开发
- [ ] 完整PDE求解器
- [ ] 自动微分引擎
- [ ] GPU加速
- [ ] 测试与文档

## 依赖安装

### Rust
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Python (使用uv)
```bash
pip install uv
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Node.js
```bash
# 使用nvm安装
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install node
```

## 许可证

MIT
