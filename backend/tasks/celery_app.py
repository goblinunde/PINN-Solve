from celery import Celery

celery_app = Celery(
    "pinn_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task
def train_pinn(config: dict):
    """异步训练任务"""
    # TODO: 调用Rust核心进行训练
    return {"status": "completed"}
