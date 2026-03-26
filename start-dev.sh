#!/bin/bash

echo "🚀 启动 PINN-Solve 开发环境"

# 启动后端
echo "📦 启动后端服务..."
cd backend
source .venv/bin/activate
python main.py &
BACKEND_PID=$!

# 等待后端启动
sleep 2

# 启动前端
echo "🎨 启动前端服务..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "✅ 服务已启动"
echo "   后端: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo "   前端: http://localhost:38000"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 捕获退出信号
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM

wait
