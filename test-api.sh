#!/bin/bash

echo "🧪 测试PINN-Solve核心功能"

# 测试后端API
echo ""
echo "📡 测试后端API..."
cd backend
source .venv/bin/activate

# 启动后端
python main.py &
BACKEND_PID=$!
sleep 3

# 测试API
echo "测试健康检查..."
curl -s http://localhost:8000/health | python -m json.tool

echo ""
echo "测试训练API..."
curl -s -X POST http://localhost:8000/api/train/ \
  -H "Content-Type: application/json" \
  -d '{"layers": [2,32,32,1], "learning_rate": 0.001, "epochs": 100, "n_points": 50}' \
  | python -m json.tool

# 停止后端
kill $BACKEND_PID

echo ""
echo "✅ 测试完成"
