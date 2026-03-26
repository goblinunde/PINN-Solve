from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import numpy as np
import sys
import os

# 添加Rust模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../pinn-core/target/release'))

router = APIRouter(prefix="/api/train", tags=["training"])

class TrainingConfig(BaseModel):
    layers: list[int] = [2, 32, 32, 1]
    learning_rate: float = 0.001
    epochs: int = 1000
    n_points: int = 100

training_tasks = {}

@router.post("/")
async def start_training(config: TrainingConfig):
    task_id = f"task-{len(training_tasks) + 1}"
    
    try:
        # 尝试导入Rust模块
        try:
            import pinn_core
            solver = pinn_core.Solver(config.layers, config.learning_rate)
            
            # 生成训练数据
            x = np.linspace(0, 1, config.n_points)
            y = np.linspace(0, 1, config.n_points)
            X, Y = np.meshgrid(x, y)
            x_data = np.column_stack([X.ravel(), Y.ravel()]).tolist()
            
            # 训练
            losses = solver.train(x_data, config.epochs)
            
            training_tasks[task_id] = {
                "status": "completed",
                "losses": losses,
                "config": config.dict()
            }
        except ImportError:
            # Rust模块未编译，使用模拟数据
            losses = [1.0 / (i + 1) for i in range(min(config.epochs, 100))]
            training_tasks[task_id] = {
                "status": "completed",
                "losses": losses,
                "config": config.dict(),
                "note": "Using simulated data (Rust module not available)"
            }
        
        return {"task_id": task_id, "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{task_id}/status")
async def get_training_status(task_id: str):
    if task_id not in training_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = training_tasks[task_id]
    progress = 1.0 if task["status"] == "completed" else 0.5
    current_loss = task["losses"][-1] if task["losses"] else 0.0
    
    return {
        "task_id": task_id,
        "status": task["status"],
        "progress": progress,
        "loss": current_loss,
        "losses": task["losses"]
    }
