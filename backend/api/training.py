from copy import deepcopy
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.training_tasks import (
    TERMINAL_STATUSES,
    counts_from_items,
    create_training_task,
    delete_task,
    get_task_detail,
    list_task_items,
    request_cancel,
    set_celery_id,
)
from tasks.celery_app import train_pinn

router = APIRouter(prefix="/api/train", tags=["training"])


class TrainingConfig(BaseModel):
    name: str = "PINN Training Task"
    pde: str | None = None
    layers: list[int] = Field(default_factory=lambda: [2, 32, 32, 1])
    learning_rate: float = 0.001
    epochs: int = 1000
    n_points: int = 256
    n_boundary: int = 128
    solver_config: dict[str, Any] | None = None


class BulkDeleteRequest(BaseModel):
    task_ids: list[str] = Field(default_factory=list)


def _legacy_pde_to_kind(pde_text: str | None) -> str:
    text = (pde_text or "").lower()
    if "burgers" in text or ("u_t" in text and "u_x" in text and "u_xx" in text):
        return "burgers_1d"
    if "heat" in text or ("u_t" in text and "u_xx" in text):
        return "heat_1d"
    if "u_xx" in text and "u_yy" in text and ("sin" in text or "= 1" in text or "=1" in text):
        return "poisson_2d"
    return "laplace_2d"


def _legacy_source_type(pde_text: str | None) -> str:
    text = (pde_text or "").lower()
    if "sin" in text:
        return "sine"
    if "= 1" in text or "=1" in text:
        return "one"
    return "zero"


def _normalize_hidden_layers(hidden_layers: list[dict] | None, legacy_layers: list[int]) -> list[dict]:
    if hidden_layers:
        normalized = []
        for layer in hidden_layers:
            normalized.append(
                {
                    "size": max(1, int(layer.get("size", 32))),
                    "activation": layer.get("activation") or "tanh",
                    "residual": bool(layer.get("residual", False)),
                }
            )
        return normalized

    if len(legacy_layers) >= 3:
        return [
            {"size": max(1, int(size)), "activation": "tanh", "residual": False}
            for size in legacy_layers[1:-1]
        ]

    return [
        {"size": 32, "activation": "tanh", "residual": False},
        {"size": 32, "activation": "tanh", "residual": False},
    ]


def _describe_pde(pde_config: dict[str, Any]) -> str:
    kind = pde_config.get("kind", "laplace_2d")

    if kind == "poisson_2d":
        source_type = pde_config.get("source_type", "zero")
        source_map = {
            "zero": "0",
            "one": "1",
            "sine": "sin(pi x) sin(pi y)",
        }
        return f"u_xx + u_yy = {source_map.get(source_type, 'f(x, y)')}"

    if kind == "heat_1d":
        alpha = float(pde_config.get("alpha", 0.1))
        return f"u_t - {alpha:g} u_xx = 0"

    if kind == "burgers_1d":
        viscosity = float(pde_config.get("viscosity", 0.01))
        return f"u_t + u u_x - {viscosity:g} u_xx = 0"

    return "u_xx + u_yy = 0"


def _normalize_training_config(raw_config: dict[str, Any]) -> dict[str, Any]:
    config = deepcopy(raw_config)
    legacy_layers = list(config.get("layers") or [2, 32, 32, 1])
    solver_config = deepcopy(config.get("solver_config") or {})

    pde_config = deepcopy(solver_config.get("pde") or {})
    pde_config["kind"] = pde_config.get("kind") or _legacy_pde_to_kind(config.get("pde"))
    pde_config["source_type"] = pde_config.get("source_type") or _legacy_source_type(config.get("pde"))
    pde_config["alpha"] = float(pde_config.get("alpha", 0.1))
    pde_config["viscosity"] = float(pde_config.get("viscosity", 0.01))

    network_config = deepcopy(solver_config.get("network") or {})
    input_dim = max(1, int(network_config.get("input_dim") or 2))
    output_dim = max(1, int(network_config.get("output_dim") or 1))
    hidden_layers = _normalize_hidden_layers(network_config.get("hidden_layers"), legacy_layers)
    output_activation = network_config.get("output_activation") or "linear"
    architecture = network_config.get("architecture") or "mlp"

    learning_rate = float(solver_config.get("learning_rate", config.get("learning_rate", 0.001)))
    n_points = max(16, int(config.get("n_points", 256)))
    n_boundary = max(8, int(config.get("n_boundary", 128)))
    collocation_batch_size = max(
        1,
        int(solver_config.get("collocation_batch_size", min(max(n_points // 2, 16), 128))),
    )

    normalized_solver_config = {
        "network": {
            "input_dim": input_dim,
            "hidden_layers": hidden_layers,
            "output_dim": output_dim,
            "output_activation": output_activation,
            "architecture": architecture,
        },
        "optimizer": solver_config.get("optimizer") or "adam",
        "learning_rate": learning_rate,
        "pde": pde_config,
        "epsilon": float(solver_config.get("epsilon", 1e-4)),
        "lambda_boundary": float(solver_config.get("lambda_boundary", 10.0)),
        "collocation_batch_size": collocation_batch_size,
    }

    layer_sizes = [
        input_dim,
        *[layer["size"] for layer in hidden_layers],
        output_dim,
    ]

    normalized = {
        **config,
        "name": config.get("name") or "PINN Training Task",
        "pde": config.get("pde") or _describe_pde(pde_config),
        "layers": layer_sizes,
        "learning_rate": learning_rate,
        "epochs": max(1, int(config.get("epochs", 1000))),
        "n_points": n_points,
        "n_boundary": n_boundary,
        "solver_config": normalized_solver_config,
    }

    return normalized


def _require_task(task_id: str) -> dict:
    task = get_task_detail(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/")
async def start_training(config: TrainingConfig):
    normalized_config = _normalize_training_config(config.model_dump())
    task = create_training_task(normalized_config)
    async_result = train_pinn.delay(task["task_id"], normalized_config)
    task = set_celery_id(task["task_id"], async_result.id)

    return {
        "task_id": task["task_id"],
        "status": "queued",
        "task": task,
    }


@router.get("/")
async def list_training_tasks():
    items = list_task_items()
    return {
        "items": items,
        "total": len(items),
        "counts": counts_from_items(items),
    }


@router.post("/bulk-delete")
async def bulk_delete_training_tasks(payload: BulkDeleteRequest):
    deleted_task_ids = []
    skipped_task_ids = []

    for task_id in payload.task_ids:
        task = get_task_detail(task_id)
        if task is None or task["status"] not in TERMINAL_STATUSES:
            skipped_task_ids.append(task_id)
            continue

        delete_task(task_id)
        deleted_task_ids.append(task_id)

    return {
        "deleted_task_ids": deleted_task_ids,
        "skipped_task_ids": skipped_task_ids,
        "deleted_count": len(deleted_task_ids),
    }


@router.get("/{task_id}")
async def get_training_task(task_id: str):
    return _require_task(task_id)


@router.get("/{task_id}/status")
async def get_training_status(task_id: str):
    return _require_task(task_id)


@router.post("/{task_id}/cancel")
async def cancel_training(task_id: str):
    task = _require_task(task_id)
    if task["status"] in TERMINAL_STATUSES:
        return {
            "task_id": task_id,
            "status": task["status"],
            "message": "Task is already finished",
        }

    updated = request_cancel(task_id)
    return {
        "task_id": task_id,
        "status": updated["status"],
        "message": "Cancellation requested",
    }


@router.post("/{task_id}/retry")
async def retry_training(task_id: str):
    task = _require_task(task_id)
    if task["status"] not in {"failed", "cancelled"}:
        raise HTTPException(status_code=409, detail="Only failed or cancelled tasks can be retried")

    retry_config = _normalize_training_config(dict(task["config"]))
    retry_config["name"] = retry_config.get("name") or task["name"]
    retry_config["pde"] = retry_config.get("pde") or task["pde"]
    retry_config["retry_of"] = task_id

    retried_task = create_training_task(retry_config)
    async_result = train_pinn.delay(retried_task["task_id"], retry_config)
    retried_task = set_celery_id(retried_task["task_id"], async_result.id)

    return {
        "task_id": retried_task["task_id"],
        "status": "queued",
        "retry_of": task_id,
        "task": retried_task,
    }


@router.delete("/{task_id}")
async def delete_training_task(task_id: str):
    task = _require_task(task_id)
    if task["status"] not in TERMINAL_STATUSES:
        raise HTTPException(status_code=409, detail="Only finished tasks can be deleted")

    delete_task(task_id)
    return {
        "task_id": task_id,
        "status": "deleted",
    }


@router.get("/{task_id}/solution")
async def get_solution(task_id: str):
    task = _require_task(task_id)
    if task["status"] != "completed" or "solution" not in task:
        raise HTTPException(status_code=409, detail="Solution is not available until the task is completed")
    return task["solution"]
