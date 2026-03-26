from services.training_tasks import counts_from_items, list_task_items, now_utc, to_iso
from data.models import WorkerState, session_scope

HEARTBEAT_TTL_SECONDS = 10


def update_worker_state(
    worker_id: str,
    *,
    status: str | None = None,
    last_task_id: str | None = None,
    last_error: str | None = None,
    started_at=None,
):
    with session_scope() as session:
        worker = session.get(WorkerState, worker_id)
        if worker is None:
            worker = WorkerState(worker_id=worker_id)

        now = now_utc()
        worker.last_heartbeat_at = now
        worker.updated_at = now

        if status is not None:
            worker.status = status
        if last_task_id is not None:
            worker.last_task_id = last_task_id
        if last_error is not None:
            worker.last_error = last_error
        if started_at is not None and worker.started_at is None:
            worker.started_at = started_at

        session.add(worker)
        session.flush()
        return serialize_worker(worker)


def serialize_worker(worker: WorkerState) -> dict:
    now = now_utc()
    heartbeat_age = None
    if worker.last_heartbeat_at is not None:
        heartbeat_age = (now - worker.last_heartbeat_at).total_seconds()

    online = (
        worker.status != "offline"
        and heartbeat_age is not None
        and heartbeat_age <= HEARTBEAT_TTL_SECONDS
    )

    return {
        "worker_id": worker.worker_id,
        "status": "online" if online else "offline",
        "last_heartbeat_at": to_iso(worker.last_heartbeat_at),
        "last_task_id": worker.last_task_id,
        "last_error": worker.last_error,
        "started_at": to_iso(worker.started_at),
        "updated_at": to_iso(worker.updated_at),
    }


def list_workers() -> list[dict]:
    with session_scope() as session:
        workers = session.query(WorkerState).all()
        return [serialize_worker(worker) for worker in workers]


def queue_overview() -> dict:
    items = list_task_items()
    counts = counts_from_items(items)
    workers = list_workers()

    return {
        "total": len(items),
        "queued": counts["queued"],
        "running": counts["running"],
        "cancelling": counts["cancelling"],
        "completed": counts["completed"],
        "failed": counts["failed"],
        "cancelled": counts["cancelled"],
        "online_workers": sum(1 for worker in workers if worker["status"] == "online"),
        "workers": len(workers),
    }
