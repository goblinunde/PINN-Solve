#!/bin/bash

echo "🧪 测试PINN-Solve核心功能"

# 测试后端API
echo ""
echo "📡 测试后端API..."
cd backend
source .venv/bin/activate

# 启动worker
python -m celery -A tasks.celery_app worker --pool solo --loglevel WARNING >/tmp/pinn-worker.log 2>&1 &
WORKER_PID=$!
sleep 2

# 启动后端
python main.py &
BACKEND_PID=$!
sleep 3

# 测试API
echo "测试健康检查..."
curl -s http://localhost:8000/health | python -m json.tool

echo ""
echo "测试训练API..."
TASK_ID=$(curl -s -X POST http://localhost:8000/api/train/ \
  -H "Content-Type: application/json" \
  -d '{"layers": [2,32,32,1], "learning_rate": 0.001, "epochs": 100, "n_points": 50}' \
  | python -c "import json,sys; print(json.load(sys.stdin)['task_id'])")

echo "任务已创建: $TASK_ID"
echo ""
echo "查询任务列表..."
curl -s http://localhost:8000/api/train/ | python -m json.tool

echo ""
echo "轮询训练状态..."
for _ in $(seq 1 20); do
  STATUS_JSON=$(curl -s "http://localhost:8000/api/train/$TASK_ID/status")
  echo "$STATUS_JSON" | python -m json.tool
  STATUS=$(echo "$STATUS_JSON" | python -c "import json,sys; print(json.load(sys.stdin)['status'])")

  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ] || [ "$STATUS" = "cancelled" ]; then
    break
  fi

  sleep 1
done

if [ "$STATUS" = "completed" ]; then
  echo ""
  echo "获取训练结果..."
  curl -s "http://localhost:8000/api/results/$TASK_ID" | python -m json.tool
fi

# 停止后端
kill $WORKER_PID
kill $BACKEND_PID

echo ""
echo "✅ 测试完成"
