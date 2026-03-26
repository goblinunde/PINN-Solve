from fastapi import APIRouter, HTTPException
from services.training_tasks import get_task_detail

router = APIRouter(prefix="/api/results", tags=["results"])

@router.get("/{task_id}")
async def get_results(task_id: str):
    task = get_task_detail(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task["status"] != "completed" or "solution" not in task:
        raise HTTPException(status_code=409, detail="Results are available only after the task is completed")

    return {
        "task_id": task_id,
        "solution": task["solution"]
    }

@router.get("/{task_id}/visualize")
async def get_visualization_data(task_id: str):
    task = get_task_detail(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task["status"] != "completed" or "solution" not in task:
        raise HTTPException(status_code=409, detail="Visualization data is available only after the task is completed")

    return task["solution"]
