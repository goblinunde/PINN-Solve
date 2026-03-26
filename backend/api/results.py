from fastapi import APIRouter, HTTPException
import numpy as np

router = APIRouter(prefix="/api/results", tags=["results"])

@router.get("/{task_id}")
async def get_results(task_id: str):
    # 生成示例解
    x = np.linspace(0, 1, 50)
    y = np.linspace(0, 1, 50)
    X, Y = np.meshgrid(x, y)
    U = np.sin(np.pi * X) * np.sin(np.pi * Y)
    
    return {
        "task_id": task_id,
        "solution": {
            "x": x.tolist(),
            "y": y.tolist(),
            "u": U.tolist()
        }
    }

@router.get("/{task_id}/visualize")
async def get_visualization_data(task_id: str):
    x = np.linspace(0, 1, 50)
    y = np.linspace(0, 1, 50)
    X, Y = np.meshgrid(x, y)
    U = np.sin(np.pi * X) * np.sin(np.pi * Y)
    
    return {
        "x": x.tolist(),
        "y": y.tolist(),
        "u": U.tolist()
    }
