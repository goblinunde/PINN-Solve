from copy import deepcopy
from datetime import datetime
from uuid import uuid4

from sqlalchemy import desc

from data.models import TrainingDataset, session_scope


def now_utc():
    return datetime.utcnow()


def generate_dataset_id():
    return f"dataset-{uuid4().hex[:8]}"


def to_iso(value):
    if value is None:
        return None
    return value.isoformat(timespec="seconds") + "Z"


def serialize_dataset(dataset: TrainingDataset, detail: bool = False) -> dict:
    payload = {
        "dataset_id": dataset.dataset_id,
        "name": dataset.name,
        "pde_kind": dataset.pde_kind,
        "input_dim": dataset.input_dim,
        "sample_count": dataset.sample_count,
        "description": dataset.description,
        "created_at": to_iso(dataset.created_at),
        "updated_at": to_iso(dataset.updated_at),
    }
    if detail:
        payload["payload"] = deepcopy(dataset.payload or {})
    return payload


def create_dataset(payload: dict) -> dict:
    dataset_id = generate_dataset_id()
    now = now_utc()
    inputs = payload.get("inputs") or []
    dataset_payload = {
        "inputs": inputs,
        "targets": payload.get("targets") or [],
        "metadata": payload.get("metadata") or {},
    }

    with session_scope() as session:
        dataset = TrainingDataset(
            dataset_id=dataset_id,
            name=payload.get("name") or "Training Dataset",
            pde_kind=payload.get("pde_kind") or "generic",
            input_dim=len(inputs[0]) if inputs else 0,
            sample_count=len(inputs),
            description=payload.get("description"),
            payload=dataset_payload,
            created_at=now,
            updated_at=now,
        )
        session.add(dataset)

    return get_dataset_detail(dataset_id)


def list_datasets() -> list[dict]:
    with session_scope() as session:
        datasets = session.query(TrainingDataset).order_by(desc(TrainingDataset.created_at)).all()
        return [serialize_dataset(dataset) for dataset in datasets]


def get_dataset_detail(dataset_id: str) -> dict | None:
    with session_scope() as session:
        dataset = session.get(TrainingDataset, dataset_id)
        if dataset is None:
            return None
        return serialize_dataset(dataset, detail=True)
