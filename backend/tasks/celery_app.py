import json
from pathlib import Path
import os
import sys
import threading
import time

import numpy as np
from celery import Celery
from celery.signals import worker_ready, worker_shutdown

from data.models import init_db
from services.training_tasks import get_task_detail, is_cancel_requested, now_utc, update_task
from services.system_status import update_worker_state

BASE_DIR = Path(__file__).resolve().parent.parent
RUNTIME_DIR = BASE_DIR / ".celery"
QUEUE_DIR = RUNTIME_DIR / "queue"
PROCESSED_DIR = RUNTIME_DIR / "processed"
CONTROL_DIR = RUNTIME_DIR / "control"
DB_PATH = BASE_DIR / "pinn_solve.db"
WORKER_NAME = None
HEARTBEAT_STOP = threading.Event()
HEARTBEAT_THREAD = None


def ensure_runtime_dirs():
    for path in [RUNTIME_DIR, QUEUE_DIR, PROCESSED_DIR, CONTROL_DIR]:
        path.mkdir(parents=True, exist_ok=True)


ensure_runtime_dirs()
init_db()

celery_app = Celery(
    "pinn_tasks",
    broker="filesystem://",
    backend=f"db+sqlite:///{DB_PATH}",
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    broker_transport_options={
        "data_folder_in": str(QUEUE_DIR),
        "data_folder_out": str(QUEUE_DIR),
        "processed_folder": str(PROCESSED_DIR),
        "control_folder": str(CONTROL_DIR),
        "store_processed": True,
    },
)

# 添加Rust模块路径
sys.path.insert(0, os.path.join(BASE_DIR, "pinn-core/target/release"))


def _heartbeat_loop():
    while not HEARTBEAT_STOP.wait(3):
        if WORKER_NAME:
            update_worker_state(WORKER_NAME, status="online")


@worker_ready.connect
def handle_worker_ready(sender=None, **kwargs):
    global WORKER_NAME, HEARTBEAT_THREAD
    WORKER_NAME = getattr(sender, "hostname", "celery-worker")
    HEARTBEAT_STOP.clear()
    update_worker_state(WORKER_NAME, status="online", started_at=now_utc(), last_error=None)
    HEARTBEAT_THREAD = threading.Thread(target=_heartbeat_loop, daemon=True)
    HEARTBEAT_THREAD.start()


@worker_shutdown.connect
def handle_worker_shutdown(sender=None, **kwargs):
    HEARTBEAT_STOP.set()
    worker_name = getattr(sender, "hostname", WORKER_NAME)
    if worker_name:
        update_worker_state(worker_name, status="offline")


def _pde_kind(config: dict) -> str:
    solver_config = config.get("solver_config") or {}
    pde_config = solver_config.get("pde") or {}
    return pde_config.get("kind") or "laplace_2d"


def _solver_input_dim(config: dict) -> int:
    solver_config = config.get("solver_config") or {}
    network_config = solver_config.get("network") or {}
    if network_config.get("input_dim"):
        return int(network_config["input_dim"])

    layers = config.get("layers") or [2, 32, 32, 1]
    return int(layers[0]) if layers else 2


def _generate_training_points(n_points: int, config: dict):
    return np.random.rand(max(n_points, 16), _solver_input_dim(config)).tolist()


def _generate_solution_from_solver(solver, config: dict):
    axis_labels = {
        "laplace_2d": ("x", "y"),
        "poisson_2d": ("x", "y"),
        "heat_1d": ("x", "t"),
        "burgers_1d": ("x", "t"),
    }
    x_test = np.linspace(0, 1, 50)
    y_test = np.linspace(0, 1, 50)
    grid_x, grid_y = np.meshgrid(x_test, y_test)
    test_points = np.column_stack([grid_x.ravel(), grid_y.ravel()]).tolist()
    u_pred = solver.predict_batch(test_points)
    U = np.array(u_pred).reshape(50, 50)
    return {
        "x": x_test.tolist(),
        "y": y_test.tolist(),
        "u": U.tolist(),
        "axes": list(axis_labels.get(_pde_kind(config), ("x", "y"))),
    }


def _generate_demo_solution(config: dict | None = None):
    x = np.linspace(0, 1, 50)
    y = np.linspace(0, 1, 50)
    X, Y = np.meshgrid(x, y)
    U = np.sin(np.pi * X) * np.sin(np.pi * Y)
    axis_labels = {
        "laplace_2d": ("x", "y"),
        "poisson_2d": ("x", "y"),
        "heat_1d": ("x", "t"),
        "burgers_1d": ("x", "t"),
    }
    return {
        "x": x.tolist(),
        "y": y.tolist(),
        "u": U.tolist(),
        "axes": list(axis_labels.get(_pde_kind(config or {}), ("x", "y"))),
    }


def _mark_cancelled(task_id: str, note: str | None = None):
    payload = {
        "status": "cancelled",
        "finished_at": now_utc(),
    }
    if note:
        payload["note"] = note
    update_task(task_id, **payload)
    if WORKER_NAME:
        update_worker_state(WORKER_NAME, status="online", last_task_id=task_id)


def _mark_failed(task_id: str, error: str):
    update_task(
        task_id,
        status="failed",
        error=error,
        finished_at=now_utc(),
    )
    if WORKER_NAME:
        update_worker_state(WORKER_NAME, status="online", last_task_id=task_id, last_error=error)


def _run_simulated_training(task_id: str, config: dict, import_error: str):
    steps = max(12, min(config["epochs"], 60))
    losses = []

    update_task(
        task_id,
        status="running",
        progress=0.02,
        mode="simulated",
        note=f"Using simulated training data because Rust module is unavailable: {import_error}",
    )

    for step in range(steps):
        if is_cancel_requested(task_id):
            _mark_cancelled(task_id, "Task was cancelled before simulated training completed.")
            return

        ratio = (step + 1) / steps
        loss = round(1.0 / (1 + step * 0.45), 6)
        losses.append(loss)
        update_task(task_id, progress=min(ratio * 0.9, 0.9), losses=list(losses))
        time.sleep(0.08)

    if is_cancel_requested(task_id):
        _mark_cancelled(task_id, "Task was cancelled before solution generation completed.")
        return

    update_task(
        task_id,
        status="completed",
        progress=1.0,
        losses=list(losses),
        solution=_generate_demo_solution(config),
        finished_at=now_utc(),
    )
    if WORKER_NAME:
        update_worker_state(WORKER_NAME, status="online", last_task_id=task_id, last_error=None)


def _run_native_training(task_id: str, config: dict):
    if is_cancel_requested(task_id):
        _mark_cancelled(task_id, "Task was cancelled before native training started.")
        return

    update_task(task_id, status="running", progress=0.05, mode="native")

    try:
        import pinn_core
    except ImportError as exc:
        _run_simulated_training(task_id, config, str(exc))
        return

    try:
        if config.get("solver_config"):
            solver = pinn_core.create_solver_from_config_json(json.dumps(config["solver_config"]))
        else:
            solver = pinn_core.Solver(config["layers"], config["learning_rate"])

        training_points = _generate_training_points(config["n_points"], config)
        update_task(task_id, progress=0.15)

        losses = [float(value) for value in solver.train(training_points, config["epochs"], config["n_boundary"])]
        if is_cancel_requested(task_id):
            _mark_cancelled(task_id, "Cancellation was requested while native training was still finishing.")
            return

        update_task(task_id, progress=0.85, losses=losses)
        solution = _generate_solution_from_solver(solver, config)

        if is_cancel_requested(task_id):
            _mark_cancelled(task_id, "Cancellation was requested before native results were stored.")
            return

        update_task(
            task_id,
            status="completed",
            progress=1.0,
            losses=losses,
            solution=solution,
            finished_at=now_utc(),
        )
        if WORKER_NAME:
            update_worker_state(WORKER_NAME, status="online", last_task_id=task_id, last_error=None)
    except Exception as exc:
        _mark_failed(task_id, str(exc))


@celery_app.task(name="tasks.train_pinn")
def train_pinn(task_id: str, config: dict):
    task = get_task_detail(task_id)
    if task is None or task["status"] == "cancelled":
        return {"task_id": task_id, "status": "skipped"}

    if WORKER_NAME:
        update_worker_state(WORKER_NAME, status="online", last_task_id=task_id)

    update_task(task_id, status="running", started_at=now_utc())
    _run_native_training(task_id, config)
    return {"task_id": task_id}
