from copy import deepcopy
from datetime import datetime
from uuid import uuid4

from sqlalchemy import desc

from data.models import TrainingTask, WorkerState, session_scope

ACTIVE_STATUSES = {"queued", "running"}
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}
WORKER_HEARTBEAT_TTL_SECONDS = 10
STALE_TASK_TIMEOUT_SECONDS = 30


def now_utc():
    return datetime.utcnow()


def generate_task_id():
    return f"task-{uuid4().hex[:8]}"


def to_iso(value):
    if value is None:
        return None
    return value.isoformat(timespec="seconds") + "Z"


def effective_status(task: TrainingTask) -> str:
    if task.cancel_requested and task.status in ACTIVE_STATUSES:
        return "cancelling"
    return task.status


def current_loss(task: TrainingTask):
    if task.losses:
        return task.losses[-1]
    return None


def _reconcile_stale_tasks(session):
    now = now_utc()
    workers = session.query(WorkerState).all()
    claimed_task_ids = {
        worker.last_task_id
        for worker in workers
        if worker.last_task_id
        and worker.status != "offline"
        and worker.last_heartbeat_at is not None
        and (now - worker.last_heartbeat_at).total_seconds() <= WORKER_HEARTBEAT_TTL_SECONDS
    }

    active_tasks = session.query(TrainingTask).filter(TrainingTask.status.in_(ACTIVE_STATUSES)).all()
    for task in active_tasks:
        if task.task_id in claimed_task_ids or task.updated_at is None:
            continue

        stale_seconds = (now - task.updated_at).total_seconds()
        if stale_seconds < STALE_TASK_TIMEOUT_SECONDS:
            continue

        if task.cancel_requested:
            task.status = "cancelled"
            task.note = task.note or "Task was cancelled after losing its worker heartbeat."
        else:
            task.status = "failed"
            task.error = task.error or "Task became orphaned because no active worker continued the job."
        task.finished_at = now
        task.updated_at = now
        session.add(task)


def serialize_task(task: TrainingTask, detail: bool = False) -> dict:
    payload = {
        "task_id": task.task_id,
        "name": task.name,
        "pde": task.pde,
        "status": effective_status(task),
        "progress": task.progress or 0.0,
        "current_loss": current_loss(task),
        "created_at": to_iso(task.created_at),
        "updated_at": to_iso(task.updated_at),
        "started_at": to_iso(task.started_at),
        "finished_at": to_iso(task.finished_at),
        "mode": task.mode or "pending",
        "has_results": bool(task.solution) and task.status == "completed",
        "can_cancel": task.status in ACTIVE_STATUSES and not task.cancel_requested,
        "can_delete": task.status in TERMINAL_STATUSES,
        "note": task.note,
        "error": task.error,
    }

    if detail:
        payload["config"] = deepcopy(task.config or {})
        payload["losses"] = list(task.losses or [])
        if task.solution:
            payload["solution"] = deepcopy(task.solution)

    return payload


def create_training_task(config: dict) -> dict:
    created_at = now_utc()
    task_id = generate_task_id()

    with session_scope() as session:
        task = TrainingTask(
            task_id=task_id,
            name=config.get("name") or "PINN Training Task",
            pde=config.get("pde") or "",
            status="queued",
            progress=0.0,
            mode="pending",
            config=deepcopy(config),
            losses=[],
            cancel_requested=False,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(task)

    return get_task_detail(task_id)


def get_task(task_id: str) -> TrainingTask | None:
    with session_scope() as session:
        return session.get(TrainingTask, task_id)


def get_task_detail(task_id: str) -> dict | None:
    with session_scope() as session:
        _reconcile_stale_tasks(session)
        task = session.get(TrainingTask, task_id)
        if task is None:
            return None
        return serialize_task(task, detail=True)


def list_task_items() -> list[dict]:
    with session_scope() as session:
        _reconcile_stale_tasks(session)
        tasks = session.query(TrainingTask).order_by(desc(TrainingTask.created_at)).all()
        return [serialize_task(task) for task in tasks]


def counts_from_items(items: list[dict]) -> dict:
    counts = {status: 0 for status in ["queued", "running", "cancelling", "completed", "failed", "cancelled"]}
    for item in items:
        counts[item["status"]] += 1
    return counts


def task_exists(task_id: str) -> bool:
    with session_scope() as session:
        return session.get(TrainingTask, task_id) is not None


def update_task(task_id: str, **updates) -> dict | None:
    with session_scope() as session:
        task = session.get(TrainingTask, task_id)
        if task is None:
            return None

        for key, value in updates.items():
            setattr(task, key, value)
        task.updated_at = now_utc()
        session.add(task)
        session.flush()
        return serialize_task(task, detail=True)


def set_celery_id(task_id: str, celery_id: str) -> dict | None:
    return update_task(task_id, celery_id=celery_id)


def request_cancel(task_id: str) -> dict | None:
    with session_scope() as session:
        task = session.get(TrainingTask, task_id)
        if task is None:
            return None

        task.cancel_requested = True
        task.updated_at = now_utc()

        if task.status == "queued":
            task.status = "cancelled"
            task.finished_at = now_utc()
            if not task.note:
                task.note = "Task was cancelled before a worker picked it up."

        session.add(task)
        session.flush()
        return serialize_task(task, detail=True)


def is_cancel_requested(task_id: str) -> bool:
    with session_scope() as session:
        task = session.get(TrainingTask, task_id)
        return bool(task and task.cancel_requested)


def delete_task(task_id: str) -> bool:
    with session_scope() as session:
        task = session.get(TrainingTask, task_id)
        if task is None:
            return False
        session.delete(task)
        return True
